# report_ingestion_service.py
import re
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

from loguru import logger

# docling/docling_core imports
from docling_core.transforms.chunker import HierarchicalChunker
from docling.document_converter import DocumentConverter

from src.embeddings.factory import EmbeddingFactory
from src.config.settings import settings


class ReportRepository:
    """
    Milvus 操作封装：连接、建表、插入、删除。
    包含两个向量字段：
      - embedding: content (TITLE+CONTENT) embedding
      - title_embedding: title-only embedding
    """
    def __init__(self, collection_name: str, embedding_dim: int):
        self.collection_name = collection_name
        self.embedding_dim = embedding_dim

        # 延迟导入 pymilvus，避免环境未安装时导入失败
        from pymilvus import connections, utility, Collection, FieldSchema, CollectionSchema, DataType

        self.connections = connections
        self.utility = utility
        self.Collection = Collection
        self.FieldSchema = FieldSchema
        self.CollectionSchema = CollectionSchema
        self.DataType = DataType

        self._connect()
        self.collection = self._get_or_create_collection()

    def _connect(self):
        try:
            self.connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                user=settings.MILVUS_USER,
                password=settings.MILVUS_PASSWORD
            )
            logger.success(f"✅ 已连接到Milvus: {settings.MILVUS_USER}@{settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        except Exception as e:
            logger.error(f"❌ 连接Milvus失败: {e}")
            raise

    def _get_or_create_collection(self):
        # 检查 collection 是否存在
        if self.utility.has_collection(self.collection_name):
            col = self.Collection(self.collection_name)
            col.load()
            logger.info(f"Collection已存在并加载: {self.collection_name}")
            return col

        # 定义字段（包含 title 与 title_embedding）
        fields = [
            self.FieldSchema(name="chunk_id", dtype=self.DataType.VARCHAR, is_primary=True, max_length=128),
            self.FieldSchema(name="embedding", dtype=self.DataType.FLOAT_VECTOR, dim=self.embedding_dim),
            self.FieldSchema(name="title_embedding", dtype=self.DataType.FLOAT_VECTOR, dim=self.embedding_dim),
            self.FieldSchema(name="chunk_text", dtype=self.DataType.VARCHAR, max_length=4096),
            self.FieldSchema(name="title", dtype=self.DataType.VARCHAR, max_length=512),
            self.FieldSchema(name="title_level", dtype=self.DataType.INT64),
            self.FieldSchema(name="report_id", dtype=self.DataType.VARCHAR, max_length=64),
            self.FieldSchema(name="company_name", dtype=self.DataType.VARCHAR, max_length=128),
            self.FieldSchema(name="company_code", dtype=self.DataType.VARCHAR, max_length=32),
            self.FieldSchema(name="report_period", dtype=self.DataType.VARCHAR, max_length=32),
            self.FieldSchema(name="chunk_type", dtype=self.DataType.VARCHAR, max_length=64),
            self.FieldSchema(name="chunk_index", dtype=self.DataType.INT64),
            self.FieldSchema(name="page_number", dtype=self.DataType.INT64),
            self.FieldSchema(name="file_path", dtype=self.DataType.VARCHAR, max_length=256),
            self.FieldSchema(name="created_at", dtype=self.DataType.INT64),
        ]

        schema = self.CollectionSchema(fields=fields, description="Financial Reports Vector Storage (with title embeddings)")

        col = self.Collection(name=self.collection_name, schema=schema)

        index_params = {
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 16, "efConstruction": 256}
        }
        col.create_index(field_name="embedding", index_params=index_params)
        # 也可为 title_embedding 创建索引（视需求与存储开销而定）
        col.load()
        logger.success(f"✅ Collection创建完成: {self.collection_name}")

        return col

    def insert_chunks(self, chunks: List[Dict], embeddings: List[List[float]], title_embeddings: List[List[float]]):
        """
        插入数据。
        entities 顺序必须与创建 schema 字段顺序一致。
        """
        try:
            entities = [
                [c["chunk_id"] for c in chunks],
                embeddings,
                title_embeddings,
                [c["chunk_text"] for c in chunks],
                [c.get("title", "") for c in chunks],
                [c.get("title_level", 0) for c in chunks],
                [c["report_id"] for c in chunks],
                [c["company_name"] for c in chunks],
                [c["company_code"] for c in chunks],
                [c["report_period"] for c in chunks],
                [c["chunk_type"] for c in chunks],
                [c["chunk_index"] for c in chunks],
                [c["page_number"] for c in chunks],
                [c["file_path"] for c in chunks],
                [c["created_at"] for c in chunks],
            ]

            self.collection.insert(entities)
            self.collection.flush()
            logger.info(f"✅ 已存储{len(chunks)}条记录到Milvus (含 title_embedding)")
        except Exception as e:
            logger.error(f"❌ 存储到Milvus失败: {e}")
            raise

    def delete_report(self, report_id: str) -> bool:
        try:
            expr = f'report_id == "{report_id}"'
            self.collection.delete(expr)
            logger.info(f"✅ 已删除财报: {report_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 删除财报失败: {e}")
            return False


class ReportIngestionService:
    """
    支持 ingest_pdf (保留旧逻辑可复用) 与优化后的 ingest_markdown。
    这里只实现 ingest_markdown 的完整流程（含 HierarchicalChunker、长短处理、标题嵌入）。
    """

    # chunk 长度阈值
    DEFAULT_MAX_CHUNK = 500
    DEFAULT_MIN_CHUNK = 80

    COLLECTION_NAME = "financial_reports"

    def __init__(self):
        self.embedding_service = None
        self._init_embedding_service()

        # Milvus repository
        self.repo = ReportRepository(collection_name=self.COLLECTION_NAME, embedding_dim=settings.EMBEDDING_DIM)

        # docling chunker related
        self.converter = DocumentConverter()
        self.hierarchical_chunker = HierarchicalChunker()

        logger.info("✅ ReportIngestionService 初始化完成")

    def _init_embedding_service(self):
        try:
            self.embedding_service = EmbeddingFactory.create_embedding_service()
            model_name = getattr(self.embedding_service, "get_model_name", lambda: "unknown")()
            logger.success(f"✅ Embedding服务初始化完成: {model_name}")
        except Exception as e:
            logger.error(f"❌ Embedding服务初始化失败: {e}")
            raise

    # ----------------------------
    # 主要方法：ingest_markdown
    # ----------------------------
    def ingest_markdown(
        self,
        markdown_path: str,
        company_name: str,
        company_code: str,
        report_period: str,
        max_chunk: Optional[int] = None,
        min_chunk: Optional[int] = None
    ) -> Dict:
        """
        Markdown -> docling -> HierarchicalChunker -> 语义切分 & 合并短片段 -> embedding(标题+内容, 标题) -> 存入Milvus

        Args:
            markdown_path: str
            company_name: str
            company_code: str
            report_period: str
            max_chunk: 可选，覆盖默认最大chunk大小
            min_chunk: 可选，覆盖默认最小chunk大小

        Returns:
            dict: ingestion result
        """
        max_chunk = max_chunk or self.DEFAULT_MAX_CHUNK
        min_chunk = min_chunk or self.DEFAULT_MIN_CHUNK

        markdown_file = Path(markdown_path)
        if not markdown_file.exists():
            raise FileNotFoundError(f"Markdown文件不存在: {markdown_path}")

        try:
            # 1. 用 docling 转换并 chunk（保留 metadata）
            doc = self.converter.convert(str(markdown_path)).document
            raw_chunks = list(self.hierarchical_chunker.chunk(doc))
            logger.info(f"Docling HierarchicalChunker 初始 chunk 数量: {len(raw_chunks)}")

            # 2. 规范化 chunks：识别标题、继承标题、按段落/句子切分超长、合并超短
            normalized_chunks = self._normalize_markdown_chunks(
                raw_chunks,
                max_chunk=max_chunk,
                min_chunk=min_chunk
            )
            logger.info(f"规范化后 chunks: {len(normalized_chunks)}")

            if not normalized_chunks:
                raise ValueError("未能从 Markdown 中提取到有效文本块")

            # 3. 构造 embedding 输入：
            #    - title_embedding_input: 仅标题
            #    - content_embedding_input: "[TITLE] ... [CONTENT] ..."（用于主embedding）
            title_inputs = [c.get("title", "") or "" for c in normalized_chunks]
            content_inputs = [f"[TITLE] {t}\n[CONTENT] {c['chunk_text']}" for t, c in zip(title_inputs, normalized_chunks)]

            # 4. 生成 embeddings（两套）
            logger.info("正在生成 title_embeddings ...")
            title_embeddings = self._generate_embeddings(title_inputs)
            logger.info("正在生成 content_embeddings ...")
            content_embeddings = self._generate_embeddings(content_inputs)

            # 5. 构造数据并写入 Milvus
            report_id = f"{company_code}_{report_period}"
            created_at = int(time.time())

            chunks_data = []
            for i, c in enumerate(normalized_chunks):
                chunks_data.append({
                    "chunk_id": self._generate_chunk_id(report_id, i),
                    "chunk_text": c["chunk_text"],
                    "title": c.get("title", ""),
                    "title_level": c.get("title_level", 0),
                    "report_id": report_id,
                    "company_name": company_name,
                    "company_code": company_code,
                    "report_period": report_period,
                    "chunk_type": "markdown",
                    "chunk_index": i,
                    "page_number": -1,
                    "file_path": markdown_path,
                    "created_at": created_at
                })

            # insert
            self.repo.insert_chunks(chunks_data, content_embeddings, title_embeddings)

            logger.success(f"✅ Markdown 摄入成功: {report_id}, chunks={len(chunks_data)}")
            return {
                "status": "success",
                "report_id": report_id,
                "company_name": company_name,
                "company_code": company_code,
                "report_period": report_period,
                "chunks_count": len(chunks_data),
                "file_path": markdown_path
            }

        except Exception as e:
            logger.error(f"❌ Markdown摄入失败: {e}")
            raise

    # ----------------------------
    # 辅助方法：规范化 chunk（标题继承、长短处理）
    # ----------------------------
    def _normalize_markdown_chunks(self, doc_chunks, max_chunk: int, min_chunk: int) -> List[Dict]:
        """
        输入：HierarchicalChunker 输出的节点列表（每个节点含 .text，可能含 metadata）
        输出：列表，每项包含 {chunk_text, title, title_level}
        """
        normalized = []
        current_title = ""
        current_title_level = 0

        for node in doc_chunks:
            text = getattr(node, "text", "")
            if not text or not text.strip():
                # 若 node 为 heading，则可能 metadata 指示
                meta = getattr(node, "metadata", {}) if hasattr(node, "metadata") else {}
                # 某些 docling heading 以 metadata 标记；若 node.text 中包含短标题也要识别
                if meta and meta.get("type") == "heading":
                    current_title = text.strip()
                    current_title_level = meta.get("level", current_title_level)
                continue

            # 尝试判断该 node 是否是 heading（有些 node 本身是 heading）
            meta = getattr(node, "metadata", {}) if hasattr(node, "metadata") else {}
            # 如果 metadata 明确表示 heading，更新 current_title 并跳过（标题自身不作为 chunk 内容）
            if meta and meta.get("type") == "heading":
                current_title = text.strip()
                current_title_level = meta.get("level", current_title_level)
                continue

            # 普通文本：按段落分割，再对段落做语义切分
            for paragraph in text.replace("\r\n", "\n").split("\n"):
                paragraph = paragraph.strip()
                if not paragraph:
                    continue

                # 如果段落不超长，直接作为候选 segment；否则进一步按句子切分
                if len(paragraph) <= max_chunk:
                    segments = [paragraph]
                else:
                    segments = self._split_by_sentence(paragraph, max_chunk)

                # 将 segments 依次合并到 normalized，同时合并过短片段到前一片段
                for seg in segments:
                    seg = seg.strip()
                    if not seg:
                        continue

                    if len(seg) < min_chunk:
                        # 合并策略：尽量合并到上一条；若无上一条则尝试合并到下一条（这里合并到上一条）
                        if normalized:
                            normalized[-1]["chunk_text"] += "\n" + seg
                        else:
                            # 没有上一条，创建新条
                            normalized.append({
                                "chunk_text": seg,
                                "title": current_title,
                                "title_level": current_title_level
                            })
                    else:
                        normalized.append({
                            "chunk_text": seg,
                            "title": current_title,
                            "title_level": current_title_level
                        })

        # 最后一次遍历：防止连续的短片段仍然存在（再次合并保障）
        merged = []
        for item in normalized:
            if not merged:
                merged.append(item)
                continue
            if len(item["chunk_text"]) < min_chunk:
                merged[-1]["chunk_text"] += "\n" + item["chunk_text"]
            else:
                merged.append(item)

        return merged

    def _split_by_sentence(self, paragraph: str, max_chunk: int) -> List[str]:
        """
        将长段落按句子切分（中文或英文），尝试保证不在句子中间截断。
        如果句子仍然超长（极端情况），则进行强制切割，但仍按字符边界切分（不会拆分半个字符）。
        """
        # 以句末标点为界（中文、英文）
        sentences = re.split(r'(?<=[。！？!?\.])\s*', paragraph)
        segments = []
        cur = ""

        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if len(cur) + len(s) <= max_chunk:
                cur = cur + s if cur else s
            else:
                if cur:
                    segments.append(cur)
                # 单句如果本身就 > max_chunk，则需要强制分割（尽量保持字符完整）
                if len(s) <= max_chunk:
                    cur = s
                else:
                    # 强制切割单句：以 max_chunk 为步长切，但尽量保留句子边界 - 这里只能按字符截断
                    start = 0
                    while start < len(s):
                        end = start + max_chunk
                        segments.append(s[start:end])
                        start = end
                    cur = ""
        if cur:
            segments.append(cur)
        return segments

    # ----------------------------
    # Embedding wrapper
    # ----------------------------
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        生成 embedding（调用外部 embedding service）
        支持批量输入，返回 list of vectors
        """
        # 过滤空文本以避免 embedding 服务报错
        sanitized = [t if t is not None else "" for t in texts]

        try:
            # 这里假设 embedding_service 有 encode 方法，支持 batch_size 与 show_progress_bar
            embeddings = self.embedding_service.encode(
                sanitized,
                batch_size=getattr(settings, "EMBEDDING_BATCH_SIZE", 32),
                show_progress_bar=False
            )
            if not embeddings or len(embeddings) != len(sanitized):
                logger.warning("embedding 数量与输入不一致，检查 embedding 服务")
            return embeddings
        except Exception as e:
            logger.error(f"生成 embeddings 失败: {e}")
            raise

    # ----------------------------
    # 实用辅助
    # ----------------------------
    def _generate_chunk_id(self, report_id: str, chunk_index: int) -> str:
        raw_id = f"{report_id}_{chunk_index}_{int(time.time())}"
        return hashlib.md5(raw_id.encode()).hexdigest()

