"""Embedding服务工厂"""
from loguru import logger

from src.embeddings.base_embedding import BaseEmbeddingService
from src.embeddings.local_embedding import LocalEmbeddingService
from src.embeddings.http_embedding import HttpEmbeddingService
from src.config.settings import settings


class EmbeddingFactory:
    """Embedding服务工厂
    
    根据配置自动创建合适的embedding服务实例
    """
    
    @staticmethod
    def create_embedding_service() -> BaseEmbeddingService:
        """创建embedding服务实例
        
        根据配置中的EMBEDDING_SERVICE_TYPE选择：
        - 'local': 使用本地SentenceTransformer模型
        - 'http': 通过HTTP接口调用远程服务
        
        Returns:
            Embedding服务实例
        """
        service_type = settings.EMBEDDING_SERVICE_TYPE.lower()
        
        if service_type == "local":
            logger.info("📊 使用本地Embedding模型服务")
            return LocalEmbeddingService()
        
        elif service_type == "http":
            logger.info("🌐 使用HTTP Embedding服务")
            return HttpEmbeddingService()
        
        else:
            raise ValueError(
                f"不支持的Embedding服务类型: {service_type}. "
                f"请设置EMBEDDING_SERVICE_TYPE为 'local' 或 'http'"
            )
    
    @staticmethod
    def get_service_info(service: BaseEmbeddingService) -> dict:
        """获取服务信息
        
        Args:
            service: embedding服务实例
            
        Returns:
            服务信息字典
        """
        return {
            "type": service.__class__.__name__,
            "model": service.get_model_name(),
            "dimension": service.get_dimension()
        }

