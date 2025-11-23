# report_ingestion_service.py
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional

from loguru import logger

from src.embeddings.factory import EmbeddingFactory
from src.config.settings import settings
from src.ingestion.markdown_chunker import MarkdownChunker

def truncate_by_bytes(text: str, max_bytes: int) -> str:
    """按字节截断字符串"""
    if not text:
        return text
    text_bytes = text.encode('utf-8')
    if len(text_bytes) <= max_bytes:
        return text
    truncated = text_bytes[:max_bytes]
    while truncated and truncated[-1] & 0x80 and not (truncated[-1] & 0x40):
        truncated = truncated[:-1]
    return truncated.decode('utf-8', errors='ignore')

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
            self.FieldSchema(name="chunk_text", dtype=self.DataType.VARCHAR, max_length=8192),
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
        col.load()
        logger.success(f"✅ Collection创建完成: {self.collection_name}")

        return col

    def insert_chunks(self, chunks: List[Dict], embeddings: List[List[float]]):
        """
        插入数据。
        entities 顺序必须与创建 schema 字段顺序一致。
        """
        try:
            entities = [
                [c["chunk_id"] for c in chunks],
                embeddings,
                [truncate_by_bytes(c["chunk_text"], 8192) for c in chunks],
                [truncate_by_bytes(c.get("title", ""), 512) for c in chunks],
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
            logger.info(f"✅ 已存储{len(chunks)}条记录到Milvus")
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
    财报摄入服务，当前实现 Markdown 摄入流程（结构化分块 + 向量入库）。
    """

    # chunk 长度阈值
    DEFAULT_MAX_CHUNK = 600
    DEFAULT_MIN_CHUNK = 300
    
    # Milvus 字段最大长度限制
    MILVUS_MAX_CHUNK_TEXT = 1024  # chunk_text 字段最大长度
    MILVUS_MAX_TITLE = 512  # title 字段最大长度

    COLLECTION_NAME = "financial_reports"

    def __init__(self):
        self.embedding_service = None
        self._init_embedding_service()

        # Milvus repository
        self.repo = ReportRepository(collection_name=self.COLLECTION_NAME, embedding_dim=settings.EMBEDDING_DIM)

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
        Markdown -> MarkdownChunker -> 标题/表格友好分块 -> embedding(标题+内容, 标题) -> 存入Milvus

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
            normalized_chunks = self._chunk_markdown_with_markdown_chunker(
                markdown_file,
                max_chunk=max_chunk
            )

            if not normalized_chunks:
                raise ValueError("未能从 Markdown 中提取到有效文本块")

            # 构造 embedding 输入：
            #    - title_embedding_input: 仅标题
            #    - content_embedding_input: "[TITLE] ... [CONTENT] ..."（用于主embedding）
            title_inputs = [c.get("title", "") or "" for c in normalized_chunks]
            content_inputs = [c.get("chunk_text", "") or "" for c in normalized_chunks]
            
            # 4. 生成 embeddings
            # logger.info("正在生成 title_embeddings ...")
            # title_embeddings = self._generate_embeddings(title_inputs)
            logger.info("正在生成 content_embeddings ...")
            content_embeddings = self._generate_embeddings([input[:1024] for input in content_inputs])

            # 5. 构造数据并写入 Milvus
            report_id = f"{company_code}_{report_period}"
            created_at = int(time.time())

            chunks_data = []
            for i, c in enumerate(normalized_chunks):
                chunk_text = truncate_by_bytes(c["chunk_text"], 8192)
                title = truncate_by_bytes(c.get("title", ""), 512)
                
                chunks_data.append({
                    "chunk_id": f"ck_{i}",
                    "chunk_text": chunk_text,
                    "title": title,
                    "title_level": c.get("title_level", 0),
                    "report_id": report_id,
                    "company_name": company_name,
                    "company_code": company_code,
                    "report_period": report_period,
                    "chunk_type": c.get("chunk_type", "markdown"),
                    "chunk_index": i,
                    "page_number": -1,
                    "file_path": markdown_path,
                    "created_at": created_at
                })

            # insert
            self.repo.insert_chunks(chunks_data, content_embeddings)

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

    def _chunk_markdown_with_markdown_chunker(self, markdown_file: Path, max_chunk: int) -> List[Dict]:
        """
        使用 MarkdownChunker 进行结构化分块。
        """
        chunker = MarkdownChunker(max_chunk_chars=max_chunk)
        raw_chunks = chunker.chunk_file(str(markdown_file))
        logger.info(f"MarkdownChunker 初始 chunk 数量: {len(raw_chunks)}")

        normalized = []
        for chunk in raw_chunks:
            chunk_text = (chunk.get("chunk_text") or "").strip()
            if not chunk_text:
                continue

            title_path = chunk.get("title_path") or []
            normalized.append({
                "chunk_text": chunk_text,
                "title": chunk.get("title") or (title_path[-1] if title_path else ""),
                "title_level": chunk.get("title_level", len(title_path)),
                "chunk_type": chunk.get("chunk_type", "other"),
            })

        logger.info(f"MarkdownChunker 规范化后 chunks: {len(normalized)}")
        return normalized

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
            embeddings = self.embedding_service.encode(
                sanitized,
                batch_size=getattr(settings, "EMBEDDING_BATCH_SIZE", 32),
                show_progress_bar=True
            )
            if not embeddings or len(embeddings) != len(sanitized):
                logger.warning("embedding 数量与输入不一致，检查 embedding 服务")
            return embeddings
        except Exception as e:
            logger.error(f"生成 embeddings 失败: {e}")
            raise


ingestion_service = ReportIngestionService()