"""HTTP Embedding服务客户端"""
import requests
from typing import List, Union
from loguru import logger

from src.embeddings.base_embedding import BaseEmbeddingService
from src.config.settings import settings


class HttpEmbeddingService(BaseEmbeddingService):
    """HTTP Embedding服务客户端
    
    通过HTTP接口调用远程或本地embedding服务
    """
    
    def __init__(self):
        """初始化HTTP客户端"""
        self.base_url = settings.EMBEDDING_API_URL
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIM
        self.timeout = settings.EMBEDDING_API_TIMEOUT
        
        # 验证服务连接
        self._validate_connection()
    
    def _validate_connection(self):
        """验证embedding服务连接"""
        try:
            logger.info(f"正在连接Embedding服务: {self.base_url}")
            
            # 发送健康检查请求
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                logger.success(f"✅ Embedding服务连接成功: {self.base_url}")
            else:
                logger.warning(f"⚠️ Embedding服务返回异常状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 无法连接到Embedding服务: {e}")
            raise ConnectionError(f"Embedding服务连接失败: {self.base_url}")
    
    def encode(
        self, 
        texts: Union[str, List[str]], 
        batch_size: int = 32,
        show_progress_bar: bool = False
    ) -> List[List[float]]:
        """通过HTTP接口生成embedding向量
        
        Args:
            texts: 单个文本或文本列表
            batch_size: 批处理大小（HTTP服务端控制）
            show_progress_bar: 是否显示进度条（暂不支持）
            
        Returns:
            embedding向量列表
        """
        try:
            # 确保texts是列表
            if isinstance(texts, str):
                texts = [texts]
                is_single = True
            else:
                is_single = False
            
            # 准备请求数据
            payload = {
                "texts": texts,
                "model": self.model_name,
                "batch_size": batch_size
            }
            
            # 发送POST请求
            response = requests.post(
                f"{self.base_url}/embeddings",
                json=payload,
                timeout=self.timeout
            )
            
            # 检查响应
            if response.status_code != 200:
                raise RuntimeError(
                    f"Embedding服务请求失败 (status={response.status_code}): {response.text}"
                )
            
            # 解析响应
            result = response.json()
            
            if "embeddings" not in result:
                raise ValueError("Embedding服务返回数据格式错误：缺少embeddings字段")
            
            embeddings = result["embeddings"]
            
            # 验证结果
            if len(embeddings) != len(texts):
                raise ValueError(
                    f"返回的embedding数量({len(embeddings)})与输入文本数量({len(texts)})不匹配"
                )
            
            logger.debug(f"✅ 通过HTTP获取了 {len(embeddings)} 个embedding向量")
            
            return embeddings
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ Embedding服务请求超时 (timeout={self.timeout}s)")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Embedding服务请求失败: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ 生成embedding失败: {e}")
            raise
    
    def get_dimension(self) -> int:
        """获取embedding维度"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return f"{self.base_url} ({self.model_name})"

