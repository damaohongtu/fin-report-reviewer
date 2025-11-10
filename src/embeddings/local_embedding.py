"""本地Embedding模型服务"""
import os
from typing import List, Union
from pathlib import Path
from loguru import logger
from sentence_transformers import SentenceTransformer
import torch

from src.embeddings.base_embedding import BaseEmbeddingService
from src.config.settings import settings


class LocalEmbeddingService(BaseEmbeddingService):
    """本地Embedding模型服务
    
    使用SentenceTransformer本地加载模型
    """
    
    def __init__(self):
        """初始化本地Embedding模型"""
        self.model = None
        self.model_name = settings.EMBEDDING_MODEL
        self.device = settings.EMBEDDING_DEVICE
        self.dimension = settings.EMBEDDING_DIM
        self._init_model()
    
    def _init_model(self):
        """初始化模型"""
        try:
            # 设置HuggingFace国内镜像
            if 'HF_ENDPOINT' not in os.environ:
                os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                logger.info("已设置HuggingFace镜像: https://hf-mirror.com")
            
            # 设置自定义缓存目录
            if settings.EMBEDDING_CACHE_DIR:
                cache_dir = Path(settings.EMBEDDING_CACHE_DIR)
                cache_dir.mkdir(parents=True, exist_ok=True)
                os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(cache_dir)
                logger.info(f"模型缓存目录: {cache_dir}")
            
            logger.info(f"正在加载本地Embedding模型: {self.model_name}")
            
            # 检测设备
            device = self.device
            if device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA不可用，切换到CPU")
                device = "cpu"
            
            # 加载模型
            model_path = self.model_name
            if Path(model_path).exists():
                logger.info(f"从本地路径加载模型: {model_path}")
            
            self.model = SentenceTransformer(
                model_path,
                device=device,
                cache_folder=settings.EMBEDDING_CACHE_DIR if settings.EMBEDDING_CACHE_DIR else None
            )
            
            logger.success(f"✅ 本地Embedding模型加载完成: {self.model_name} (设备: {device})")
            
        except Exception as e:
            logger.error(f"❌ 加载本地Embedding模型失败: {e}")
            raise
    
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
            embedding向量列表
        """
        try:
            # 确保texts是列表
            if isinstance(texts, str):
                texts = [texts]
            
            # 使用模型生成embeddings
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=show_progress_bar,
                convert_to_numpy=True
            )
            
            # 转换为列表格式
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"❌ 生成embedding失败: {e}")
            raise
    
    def get_dimension(self) -> int:
        """获取embedding维度"""
        return self.dimension
    
    def get_model_name(self) -> str:
        """获取模型名称"""
        return self.model_name

