"""向量检索器 - 从Milvus检索相关财报信息"""
from typing import List, Dict, Optional
from loguru import logger
from pymilvus import connections, Collection
from sentence_transformers import SentenceTransformer

from src.config.settings import settings


class VectorRetriever:
    """向量检索器
    
    职责：
    1. 从Milvus检索相关财报信息
    2. 提供多种检索策略
    3. 为财报分析提供上下文
    """
    
    def __init__(self):
        """初始化检索器"""
        self._connect_milvus()
        self._init_embedding_model()
        logger.info("向量检索器初始化完成")
    
    def _connect_milvus(self):
        """连接Milvus"""
        try:
            connections.connect(
                alias="default",
                host=settings.MILVUS_HOST,
                port=settings.MILVUS_PORT,
                user=settings.MILVUS_USER,
                password=settings.MILVUS_PASSWORD
            )
            self.collection = Collection(settings.MILVUS_COLLECTION_NAME)
            self.collection.load()
            logger.success(f"✅ Milvus连接成功: {settings.MILVUS_COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"❌ Milvus连接失败: {e}")
            raise
    
    def _init_embedding_model(self):
        """初始化Embedding模型"""
        try:
            self.embedding_model = SentenceTransformer(
                settings.EMBEDDING_MODEL,
                device='cpu'  # 检索时使用CPU即可
            )
            logger.success(f"✅ Embedding模型加载完成")
        except Exception as e:
            logger.error(f"❌ Embedding模型加载失败: {e}")
            raise
    
    def _generate_embedding(self, text: str) -> List[float]:
        """生成文本embedding"""
        embedding = self.embedding_model.encode([text])[0]
        return embedding.tolist()
    
    def retrieve_by_company(
        self,
        company_name: str,
        top_k: int = 10
    ) -> List[Dict]:
        """根据公司名称检索财报
        
        Args:
            company_name: 公司名称
            top_k: 返回结果数量
            
        Returns:
            检索结果列表
        """
        logger.info(f"检索公司财报: {company_name}")
        
        try:
            query_vector = self._generate_embedding(company_name)
            
            search_results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param={"metric_type": "COSINE", "params": {"ef": 64}},
                limit=top_k,
                expr=f'company_name == "{company_name}"',
                output_fields=["report_id", "company_name", "company_code", 
                              "report_period", "chunk_type", "chunk_text"]
            )
            
            results = []
            for hits in search_results:
                for hit in hits:
                    results.append({
                        "score": hit.score,
                        "report_id": hit.entity.get("report_id"),
                        "company_name": hit.entity.get("company_name"),
                        "company_code": hit.entity.get("company_code"),
                        "report_period": hit.entity.get("report_period"),
                        "chunk_type": hit.entity.get("chunk_type"),
                        "text": hit.entity.get("chunk_text")
                    })
            
            logger.success(f"✅ 检索到 {len(results)} 条相关财报")
            return results
            
        except Exception as e:
            logger.error(f"❌ 检索失败: {e}")
            return []
    
    def retrieve_by_period(
        self,
        company_name: str,
        report_period: str
    ) -> List[Dict]:
        """检索指定期间的财报
        
        Args:
            company_name: 公司名称
            report_period: 报告期
            
        Returns:
            检索结果列表
        """
        logger.info(f"检索财报: {company_name} - {report_period}")
        
        try:
            query_vector = self._generate_embedding(f"{company_name} {report_period}")
            
            search_results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param={"metric_type": "COSINE", "params": {"ef": 64}},
                limit=50,
                expr=f'company_name == "{company_name}" and report_period == "{report_period}"',
                output_fields=["report_id", "company_name", "company_code", 
                              "report_period", "chunk_type", "chunk_text"]
            )
            
            results = []
            for hits in search_results:
                for hit in hits:
                    results.append({
                        "score": hit.score,
                        "report_id": hit.entity.get("report_id"),
                        "company_name": hit.entity.get("company_name"),
                        "company_code": hit.entity.get("company_code"),
                        "report_period": hit.entity.get("report_period"),
                        "chunk_type": hit.entity.get("chunk_type"),
                        "text": hit.entity.get("chunk_text")
                    })
            
            logger.success(f"✅ 检索到 {len(results)} 条财报数据")
            return results
            
        except Exception as e:
            logger.error(f"❌ 检索失败: {e}")
            return []
    
    def retrieve_historical_reports(
        self,
        company_name: str,
        current_period: str,
        num_periods: int = 4
    ) -> Dict[str, List[Dict]]:
        """检索历史财报数据
        
        Args:
            company_name: 公司名称
            current_period: 当前报告期
            num_periods: 检索期数
            
        Returns:
            按报告期分组的历史财报字典
        """
        logger.info(f"检索历史财报: {company_name}, 最近{num_periods}期")
        
        try:
            query_vector = self._generate_embedding(company_name)
            
            # 检索该公司的所有财报
            search_results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param={"metric_type": "COSINE", "params": {"ef": 64}},
                limit=num_periods * 20,  # 每期可能有多个chunk
                expr=f'company_name == "{company_name}"',
                output_fields=["report_id", "company_name", "company_code", 
                              "report_period", "chunk_type", "chunk_text"]
            )
            
            # 按报告期分组
            grouped_results = {}
            for hits in search_results:
                for hit in hits:
                    period = hit.entity.get('report_period')
                    if period and period not in grouped_results:
                        grouped_results[period] = []
                    if period:
                        grouped_results[period].append({
                            "score": hit.score,
                            "report_id": hit.entity.get("report_id"),
                            "company_name": hit.entity.get("company_name"),
                            "company_code": hit.entity.get("company_code"),
                            "report_period": hit.entity.get("report_period"),
                            "chunk_type": hit.entity.get("chunk_type"),
                            "text": hit.entity.get("chunk_text")
                        })
            
            logger.success(f"✅ 检索到 {len(grouped_results)} 个报告期的数据")
            return grouped_results
            
        except Exception as e:
            logger.error(f"❌ 检索历史财报失败: {e}")
            return {}
    
    def retrieve_similar_content(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Dict]:
        """检索相似内容
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            
        Returns:
            相似内容列表
        """
        logger.info(f"检索相似内容: {query[:50]}...")
        
        try:
            query_vector = self._generate_embedding(query)
            
            search_results = self.collection.search(
                data=[query_vector],
                anns_field="embedding",
                param={"metric_type": "COSINE", "params": {"ef": 64}},
                limit=top_k,
                output_fields=["report_id", "company_name", "company_code", 
                              "report_period", "chunk_type", "chunk_text"]
            )
            
            results = []
            for hits in search_results:
                for hit in hits:
                    results.append({
                        "score": hit.score,
                        "report_id": hit.entity.get("report_id"),
                        "company_name": hit.entity.get("company_name"),
                        "company_code": hit.entity.get("company_code"),
                        "report_period": hit.entity.get("report_period"),
                        "chunk_type": hit.entity.get("chunk_type"),
                        "text": hit.entity.get("chunk_text")
                    })
            
            logger.success(f"✅ 检索到 {len(results)} 条相似内容")
            return results
            
        except Exception as e:
            logger.error(f"❌ 检索失败: {e}")
            return []
    
    def get_context_for_analysis(
        self,
        company_name: str,
        report_period: str,
        query: Optional[str] = None
    ) -> str:
        """获取用于分析的上下文
        
        Args:
            company_name: 公司名称
            report_period: 报告期
            query: 可选的查询文本
            
        Returns:
            组装好的上下文文本
        """
        logger.info(f"获取分析上下文: {company_name} - {report_period}")
        
        # 检索当前期财报
        current_results = self.retrieve_by_period(company_name, report_period)
        
        # 检索历史财报
        historical_results = self.retrieve_historical_reports(company_name, report_period, num_periods=2)
        
        # 如果有特定查询，检索相关内容
        similar_results = []
        if query:
            similar_results = self.retrieve_similar_content(query, top_k=3)
        
        # 组装上下文
        context_parts = []
        
        if current_results:
            context_parts.append("=== 当前期财报 ===")
            for result in current_results[:5]:
                context_parts.append(result.get('text', ''))
        
        if historical_results:
            context_parts.append("\n=== 历史财报对比 ===")
            for period, results in list(historical_results.items())[:2]:
                if period != report_period:
                    context_parts.append(f"\n{period}:")
                    for result in results[:3]:
                        context_parts.append(result.get('text', ''))
        
        if similar_results:
            context_parts.append("\n=== 相关参考 ===")
            for result in similar_results:
                context_parts.append(result.get('text', ''))
        
        context = "\n".join(context_parts)
        logger.success(f"✅ 上下文组装完成，总长度: {len(context)} 字符")
        
        return context

