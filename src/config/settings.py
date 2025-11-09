"""配置管理模块"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目基础配置
    APP_NAME: str = "财报点评系统"
    APP_VERSION: str = "1.0.0"
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    # LLM 配置 - DeepSeek
    DEEPSEEK_API_KEY: str = Field(..., env="DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL: str = Field(default="https://api.deepseek.com", env="DEEPSEEK_BASE_URL")
    DEEPSEEK_MODEL: str = Field(default="deepseek-chat", env="DEEPSEEK_MODEL")
    DEEPSEEK_TEMPERATURE: float = Field(default=0.1, env="DEEPSEEK_TEMPERATURE")
    DEEPSEEK_MAX_TOKENS: int = Field(default=4000, env="DEEPSEEK_MAX_TOKENS")
    
    # Embedding 配置 - 本地模型
    EMBEDDING_MODEL: str = Field(default="BAAI/bge-large-zh-v1.5", env="EMBEDDING_MODEL")  # 模型名或本地路径
    EMBEDDING_DIM: int = Field(default=1024, env="EMBEDDING_DIM")  # bge-large-zh-v1.5维度
    EMBEDDING_DEVICE: str = Field(default="cuda", env="EMBEDDING_DEVICE")  # cuda 或 cpu
    EMBEDDING_BATCH_SIZE: int = Field(default=32, env="EMBEDDING_BATCH_SIZE")  # 批量处理大小
    EMBEDDING_CACHE_DIR: Optional[str] = Field(default=None, env="EMBEDDING_CACHE_DIR")  # 模型缓存目录
    
    # 数据库配置
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_ECHO: bool = Field(default=False, env="DATABASE_ECHO")
    
    # 向量数据库配置 - Milvus
    MILVUS_HOST: str = Field(default="localhost", env="MILVUS_HOST")
    MILVUS_PORT: int = Field(default=19530, env="MILVUS_PORT")
    MILVUS_USER: str = Field(..., env="MILVUS_USER")  # 必需
    MILVUS_PASSWORD: str = Field(..., env="MILVUS_PASSWORD")  # 必需
    MILVUS_COLLECTION_NAME: str = Field(default="financial_reports", env="MILVUS_COLLECTION_NAME")
    
    # 日志配置
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 数据源配置
    DATA_SOURCE: str = Field(default="excel", env="DATA_SOURCE")  # database 或 excel
    EXCEL_DATA_DIR: Path = Field(default=Path("./data/excel_reports"), env="EXCEL_DATA_DIR")
    
    # API 配置
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_RELOAD: bool = Field(default=True, env="API_RELOAD")
    
    # 文件存储配置
    UPLOAD_DIR: Path = Field(default=Path("./data/uploads"), env="UPLOAD_DIR")
    REPORT_OUTPUT_DIR: Path = Field(default=Path("./data/reports"), env="REPORT_OUTPUT_DIR")
    PDF_STORAGE_DIR: Path = Field(default=Path("./data/pdfs"), env="PDF_STORAGE_DIR")
    
    # 缓存配置
    ENABLE_CACHE: bool = Field(default=True, env="ENABLE_CACHE")
    CACHE_TTL: int = Field(default=3600, env="CACHE_TTL")
    
    # Streamlit 配置
    STREAMLIT_PORT: int = Field(default=8501, env="STREAMLIT_PORT")
    API_BASE_URL: str = Field(default="http://localhost:8000", env="API_BASE_URL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 创建必要的目录
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        self.REPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.PDF_STORAGE_DIR.mkdir(parents=True, exist_ok=True)


# 全局配置实例
settings = Settings()

