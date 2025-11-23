"""Embedding服务抽象基类"""
from abc import ABC, abstractmethod
from typing import List, Union


class BaseEmbeddingService(ABC):
    """Embedding服务抽象基类
    
    定义统一的embedding生成接口，支持不同的实现方式：
    - 本地模型（SentenceTransformer）
    - HTTP服务（远程embedding服务）
    """
    
    @abstractmethod
    def encode(
        self, 
        texts: Union[str, List[str]], 
        batch_size: int = 32,
        show_progress_bar: bool = False
    ) -> List[List[float]]:
        """生成文本的embedding向量
        
        Args:
            texts: 单个文本或文本列表
            batch_size: 批处理大小
            show_progress_bar: 是否显示进度条
            
        Returns:
            embedding向量列表，每个向量是float列表
        """
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """获取embedding维度
        
        Returns:
            向量维度
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """获取模型名称
        
        Returns:
            模型名称或服务地址
        """
        pass

