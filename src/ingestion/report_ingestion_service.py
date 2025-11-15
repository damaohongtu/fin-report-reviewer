"""PDF财报摄入服务 - 单一职责：解析PDF并存储到Milvus"""
import hashlib
import time
from typing import Dict, List, Optional
from pathlib import Path
from loguru import logger
from docling_core.transforms.chunker import HierarchicalChunker
from docling.document_converter import DocumentConverter


from src.parsers.financial_pdf_parser import FinancialPDFParser
from src.config.settings import settings
from src.embeddings.factory import EmbeddingFactory


class ReportIngestionService:
    """PDF财报摄入服务
    
    单一职责：
    1. 解析PDF财报文件
    2. 提取结构化文本块
    3. 生成向量embeddings
    4. 存储到Milvus向量数据库
    
    Milvus Collection Schema:
    - chunk_id: VARCHAR(128) - 文本块唯一ID（主键）
    - embedding: FLOAT_VECTOR - 文本向量
    - chunk_text: VARCHAR(4096) - 原始文本
    - report_id: VARCHAR(64) - 财报ID
    - company_name: VARCHAR(128) - 公司名称
    - company_code: VARCHAR(32) - 公司代码
    - report_period: VARCHAR(32) - 报告期
    - chunk_type: VARCHAR(64) - 文本块类型
    - chunk_index: INT64 - 序号
    - page_number: INT64 - 页码
    - file_path: VARCHAR(256) - 源文件路径
    - created_at: INT64 - 创建时间戳
    """
    
    # 文本块类型枚举（财报文本章节）
    CHUNK_TYPE_FULL_TEXT = "full_text"  # 通用文本
    CHUNK_TYPE_SUMMARY = "summary"  # 重要提示/摘要
    CHUNK_TYPE_BUSINESS_OVERVIEW = "business_overview"  # 公司基本情况
    CHUNK_TYPE_MANAGEMENT_DISCUSSION = "management_discussion"  # 经营情况讨论与分析
    CHUNK_TYPE_IMPORTANT_MATTERS = "important_matters"  # 重要事项
    CHUNK_TYPE_SHARE_CHANGES = "share_changes"  # 股本变动及股东情况
    CHUNK_TYPE_CORPORATE_GOVERNANCE = "corporate_governance"  # 公司治理
    CHUNK_TYPE_NOTES = "notes"  # 其他附注
    
    # Collection配置
    COLLECTION_NAME = "financial_reports"
    CHUNK_SIZE = 500  # 文本分块大小
    
    def __init__(self):
        """初始化摄入服务"""
        from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
        
        self.pdf_parser = FinancialPDFParser()
        self.connections = connections
        self.Collection = Collection
        self.FieldSchema = FieldSchema
        self.CollectionSchema = CollectionSchema
        self.DataType = DataType
        
        # 初始化Embedding服务
        self._init_embedding_service()
        
        # 连接Milvus
        self._connect_milvus()
        
        # 初始化或获取Collection
        self.collection = self._init_collection()
        
        logger.info(f"✅ PDF财报摄入服务初始化完成 - Collection: {self.COLLECTION_NAME}")
    
    def _init_embedding_service(self):
        """初始化Embedding服务"""
        try:
            self.embedding_service = EmbeddingFactory.create_embedding_service()
            logger.success(f"✅ Embedding服务初始化完成: {self.embedding_service.get_model_name()}")
        except Exception as e:
            logger.error(f"❌ Embedding服务初始化失败: {e}")
            raise
    
    def _connect_milvus(self):
        """连接到Milvus服务器（使用账号密码认证）"""
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
    
    def _init_collection(self):
        """初始化或获取Milvus Collection"""
        from pymilvus import utility
        
        # 检查Collection是否存在
        if utility.has_collection(self.COLLECTION_NAME):
            logger.info(f"Collection已存在: {self.COLLECTION_NAME}")
            collection = self.Collection(self.COLLECTION_NAME)
            collection.load()
            return collection
        
        # 创建新Collection
        logger.info(f"创建新Collection: {self.COLLECTION_NAME}")
        
        # 定义字段
        fields = [
            self.FieldSchema(name="chunk_id", dtype=self.DataType.VARCHAR, is_primary=True, max_length=128),
            self.FieldSchema(name="embedding", dtype=self.DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIM),
            self.FieldSchema(name="chunk_text", dtype=self.DataType.VARCHAR, max_length=4096),
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
        
        # 创建Schema
        schema = self.CollectionSchema(
            fields=fields,
            description="Financial Reports Vector Storage"
        )
        
        # 创建Collection
        collection = self.Collection(
            name=self.COLLECTION_NAME,
            schema=schema
        )
        
        # 创建索引
        index_params = {
            "index_type": "HNSW",
            "metric_type": "COSINE",
            "params": {"M": 16, "efConstruction": 256}
        }
        collection.create_index(field_name="embedding", index_params=index_params)
        
        # 加载Collection
        collection.load()
        
        logger.success(f"✅ Collection创建完成: {self.COLLECTION_NAME}")
        return collection
    
    def ingest_pdf(
        self, 
        pdf_path: str,
        company_name: str,
        company_code: str,
        report_period: str
    ) -> Dict:
        """从PDF摄入财报
        
        Args:
            pdf_path: PDF文件路径
            company_name: 公司名称
            company_code: 公司代码（如：600000.SH）
            report_period: 报告期（如：2024Q3, 2024-12-31）
            
        Returns:
            摄入结果字典
        """
        logger.info(f"开始摄入PDF财报: {company_name} ({report_period})")
        
        try:
            # 1. 验证文件
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            # 2. 解析PDF
            logger.info("正在解析PDF...")
            parsed_data = self.pdf_parser.parse_financial_report(pdf_path)
            
            # 3. 提取文本块
            logger.info("正在提取文本块...")
            chunks = self._extract_chunks(
                parsed_data=parsed_data,
                company_name=company_name,
                company_code=company_code,
                report_period=report_period,
                file_path=pdf_path
            )
            
            if not chunks:
                raise ValueError("未能从PDF中提取到有效文本块")
            
            # 4. 生成embeddings
            logger.info(f"正在生成embeddings ({len(chunks)}个文本块)...")
            embeddings = self._generate_embeddings([c["chunk_text"] for c in chunks])
            
            # 5. 存储到Milvus
            logger.info("正在存储到Milvus...")
            self._store_to_milvus(chunks, embeddings)
            
            report_id = f"{company_code}_{report_period}"
            logger.success(f"✅ PDF财报摄入完成: {report_id}, 共{len(chunks)}个文本块")
            
            return {
                "status": "success",
                "report_id": report_id,
                "company_name": company_name,
                "company_code": company_code,
                "report_period": report_period,
                "chunks_count": len(chunks),
                "file_path": pdf_path
            }
            
        except Exception as e:
            logger.error(f"❌ PDF财报摄入失败: {e}")
            raise
    
    def ingest_markdown(self, markdown_path: str, company_name: str, company_code: str, report_period: str) -> Dict:
        """从Markdown摄入财报, 基于docling进行chunk
        
        Args:
            markdown_path: Markdown文件路径
            company_name: 公司名称
            company_code: 公司代码
            report_period: 报告期
        """
        try:
            markdown_file = Path(markdown_path)
            if not markdown_file.exists():
                raise FileNotFoundError(f"Markdown文件不存在: {markdown_path}")
            
            converter = DocumentConverter()
            doc = converter.convert(markdown_path).document
            chunker = HierarchicalChunker()
            chunks = [chunk.text for chunk in chunker.chunk(doc)]
            logger.info(f"从Markdown摄入财报完成, 共{len(chunks)}个文本块")
            embeddings = self._generate_embeddings(chunks)
            self._store_to_milvus(chunks, embeddings)
            return {
                "status": "success",
                "report_id": f"{company_code}_{report_period}",
                "company_name": company_name,
                "company_code": company_code,
                "report_period": report_period,
            }

        except Exception as e:
            logger.error(f"❌ 从Markdown摄入财报失败: {e}")
            raise

    
    def batch_ingest(self, pdf_list: List[Dict]) -> List[Dict]:
        """批量摄入PDF财报
        
        Args:
            pdf_list: PDF文件信息列表，每项包含:
                - pdf_path: PDF文件路径
                - company_name: 公司名称
                - company_code: 公司代码
                - report_period: 报告期
            
        Returns:
            摄入结果列表
        """
        logger.info(f"开始批量摄入，共{len(pdf_list)}份财报")
        
        results = []
        for idx, item in enumerate(pdf_list, 1):
            try:
                logger.info(f"[{idx}/{len(pdf_list)}] 处理: {item.get('company_name')}")
                result = self.ingest_pdf(**item)
                results.append(result)
            except Exception as e:
                logger.error(f"[{idx}/{len(pdf_list)}] 处理失败: {e}")
                results.append({
                    "status": "failed",
                    "error": str(e),
                    **item
                })
        
        success_count = sum(1 for r in results if r.get("status") == "success")
        logger.info(f"批量摄入完成: 成功{success_count}/{len(pdf_list)}")
        
        return results
    
    def delete_report(self, report_id: str) -> bool:
        """删除指定财报的所有文本块
        
        Args:
            report_id: 财报ID
            
        Returns:
            是否删除成功
        """
        try:
            expr = f'report_id == "{report_id}"'
            self.collection.delete(expr)
            logger.info(f"✅ 已删除财报: {report_id}")
            return True
        except Exception as e:
            logger.error(f"❌ 删除财报失败: {e}")
            return False
    
    def _extract_chunks(
        self,
        parsed_data: Dict,
        company_name: str,
        company_code: str,
        report_period: str,
        file_path: str
    ) -> List[Dict]:
        """从解析的PDF数据中提取文本块（仅文本内容，不包括表格）
        
        Args:
            parsed_data: PDF解析数据
            company_name: 公司名称
            company_code: 公司代码
            report_period: 报告期
            file_path: 文件路径
            
        Returns:
            文本块列表
        """
        chunks = []
        report_id = f"{company_code}_{report_period}"
        created_at = int(time.time())
        chunk_index = 0
        
        # 提取PDF中的全部文本内容
        if 'text' in parsed_data and parsed_data['text']:
            full_text = parsed_data['text']
            
            # 按固定大小分割文本（保持上下文连贯性）
            text_chunks = self._split_text_smart(full_text, self.CHUNK_SIZE)
            
            for text in text_chunks:
                if text.strip() and len(text.strip()) > 20:  # 过滤太短的文本
                    # 智能识别文本类型（基于关键词）
                    chunk_type = self._identify_chunk_type(text)
                    
                    chunk_id = self._generate_chunk_id(report_id, chunk_index)
                    chunks.append({
                        "chunk_id": chunk_id,
                        "chunk_text": text.strip(),
                        "report_id": report_id,
                        "company_name": company_name,
                        "company_code": company_code,
                        "report_period": report_period,
                        "chunk_type": chunk_type,
                        "chunk_index": chunk_index,
                        "page_number": -1,  # 如果PDF解析器提供页码信息，可以在这里使用
                        "file_path": file_path,
                        "created_at": created_at
                    })
                    chunk_index += 1
        
        if not chunks:
            logger.warning("未提取到有效文本内容")
        
        return chunks
    
    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """生成文本embeddings
        
        Args:
            texts: 文本列表
            
        Returns:
            embeddings向量列表
        """
        try:
            logger.info(f"正在生成{len(texts)}个文本的embeddings...")
            
            # 使用embedding服务批量生成embeddings
            embeddings = self.embedding_service.encode(
                texts,
                batch_size=settings.EMBEDDING_BATCH_SIZE,
                show_progress_bar=True
            )
            
            logger.success(f"✅ 生成了{len(embeddings)}个embeddings (维度: {len(embeddings[0])})")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ 生成embeddings失败: {e}")
            raise
    
    def _store_to_milvus(self, chunks: List[Dict], embeddings: List[List[float]]):
        """存储数据到Milvus
        
        Args:
            chunks: 文本块列表
            embeddings: embeddings列表
        """
        try:
            # 准备插入数据
            entities = [
                [c["chunk_id"] for c in chunks],
                embeddings,
                [c["chunk_text"] for c in chunks],
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
            
            # 插入数据
            self.collection.insert(entities)
            self.collection.flush()
            
            logger.info(f"✅ 已存储{len(chunks)}条记录到Milvus")
            
        except Exception as e:
            logger.error(f"❌ 存储到Milvus失败: {e}")
            raise
    
    def _generate_chunk_id(self, report_id: str, chunk_index: int) -> str:
        """生成唯一的chunk_id
        
        Args:
            report_id: 财报ID
            chunk_index: 文本块索引
            
        Returns:
            chunk_id
        """
        raw_id = f"{report_id}_{chunk_index}_{int(time.time())}"
        return hashlib.md5(raw_id.encode()).hexdigest()
    
    def _split_text_smart(self, text: str, chunk_size: int, overlap: int = 50) -> List[str]:
        """智能分割长文本，尽量在段落边界分割
        
        Args:
            text: 原始文本
            chunk_size: 每块大小
            overlap: 重叠字符数（保持上下文连贯）
            
        Returns:
            文本块列表
        """
        chunks = []
        
        # 按段落分割（中文段落通常用换行或句号分隔）
        paragraphs = text.replace('\r\n', '\n').split('\n')
        
        current_chunk = ""
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 如果当前段落加入后超过chunk_size
            if len(current_chunk) + len(paragraph) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                    # 保留重叠部分
                    current_chunk = current_chunk[-overlap:] + "\n" + paragraph
                else:
                    # 单个段落太长，强制分割
                    for i in range(0, len(paragraph), chunk_size - overlap):
                        chunk = paragraph[i:i + chunk_size]
                        chunks.append(chunk)
                    current_chunk = paragraph[-overlap:] if len(paragraph) > overlap else paragraph
            else:
                current_chunk += "\n" + paragraph if current_chunk else paragraph
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def _identify_chunk_type(self, text: str) -> str:
        """根据文本内容识别chunk类型
        
        Args:
            text: 文本内容
            
        Returns:
            chunk类型
        """
        text_lower = text.lower()
        
        # 关键词匹配
        if any(kw in text for kw in ["重要提示", "摘要", "基本情况", "主要会计数据"]):
            return self.CHUNK_TYPE_SUMMARY
        elif any(kw in text for kw in ["公司基本情况", "主营业务", "行业情况"]):
            return self.CHUNK_TYPE_BUSINESS_OVERVIEW
        elif any(kw in text for kw in ["经营情况讨论", "管理层讨论", "经营分析", "财务状况分析"]):
            return self.CHUNK_TYPE_MANAGEMENT_DISCUSSION
        elif any(kw in text for kw in ["重要事项", "重大事项", "承诺事项", "诉讼事项"]):
            return self.CHUNK_TYPE_IMPORTANT_MATTERS
        elif any(kw in text for kw in ["股本变动", "股东情况", "前十名股东", "控股股东"]):
            return self.CHUNK_TYPE_SHARE_CHANGES
        elif any(kw in text for kw in ["公司治理", "董事会", "监事会", "内部控制"]):
            return self.CHUNK_TYPE_CORPORATE_GOVERNANCE
        else:
            return self.CHUNK_TYPE_FULL_TEXT


# 全局实例
ingestion_service = ReportIngestionService()

