"""
HTTP Embedding服务

提供HTTP接口的embedding服务，供财报点评系统调用
使用FastAPI + SentenceTransformer实现

启动方式：
python emb-server/embedding_server.py --host 0.0.0.0 --port 8080 --device cuda --cache-dir ./models

或使用uvicorn：
uvicorn embedding_server:app --host 0.0.0.0 --port 8080 --reload

参数说明：
--host: 服务host (默认: 0.0.0.0)
--port: 服务端口 (默认: 8080)
--model: 模型名称或路径 (默认: BAAI/bge-base-zh-v1.5)
--device: 运行设备 cuda/cpu (默认: cuda if available)
--cache-dir: 模型缓存目录 (可选，指定后会将模型下载到该目录)
--workers: 工作进程数 (默认: 1)
--reload: 开启热重载，用于开发模式
"""

import argparse
import os
from typing import List, Optional
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
import torch
from loguru import logger

# ==================== 配置 ====================
DEFAULT_MODEL = "BAAI/bge-base-zh-v1.5"
DEFAULT_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DEFAULT_BATCH_SIZE = 32
DEFAULT_CACHE_DIR = None  # 默认使用系统缓存目录

# ==================== API模型 ====================

class EmbeddingRequest(BaseModel):
    """Embedding请求"""
    texts: List[str] = Field(..., description="文本列表", min_items=1)
    model: Optional[str] = Field(default=DEFAULT_MODEL, description="模型名称")
    batch_size: Optional[int] = Field(default=DEFAULT_BATCH_SIZE, description="批处理大小")

class EmbeddingResponse(BaseModel):
    """Embedding响应"""
    embeddings: List[List[float]] = Field(..., description="向量列表")
    model: str = Field(..., description="模型名称")
    dimension: int = Field(..., description="向量维度")
    count: int = Field(..., description="向量数量")

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    model: str = Field(..., description="当前加载的模型")
    dimension: int = Field(..., description="向量维度")
    device: str = Field(..., description="运行设备")
    cache_dir: Optional[str] = Field(None, description="缓存目录")

# ==================== FastAPI应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # Startup: 初始化模型
    logger.info("🚀 Embedding服务启动中...")
    if embedding_model is None:
        logger.info("检测到通过uvicorn直接启动，使用默认配置初始化模型")
        # 使用默认模型和设备，不指定cache_dir（使用系统默认）
        init_model(DEFAULT_MODEL, DEFAULT_DEVICE, cache_folder=None)
    yield
    # Shutdown: 清理资源（如果需要）
    logger.info("🛑 Embedding服务关闭中...")

app = FastAPI(
    title="Embedding Service",
    description="提供文本向量化服务",
    version="1.0.0",
    lifespan=lifespan
)

# 全局变量
embedding_model: Optional[SentenceTransformer] = None
model_name: str = DEFAULT_MODEL
device: str = DEFAULT_DEVICE
dimension: int = 768  # bge-base-zh-v1.5 的维度
cache_dir: Optional[str] = None


def init_model(model_path: str, device_name: str, cache_folder: Optional[str] = None):
    """初始化embedding模型"""
    global embedding_model, model_name, device, dimension, cache_dir
    
    try:
        logger.info(f"正在加载Embedding模型: {model_path}")
        logger.info(f"设备: {device_name}")
        
        # 检查是否为本地路径
        is_local_path = Path(model_path).exists()
        
        if is_local_path:
            # 本地路径：直接从指定路径加载，不使用cache_folder
            logger.info(f"📂 检测到本地模型路径: {model_path}")
            model_abs_path = str(Path(model_path).resolve())
            logger.info(f"📂 绝对路径: {model_abs_path}")
            cache_dir = str(Path(model_path).parent.resolve())  # 记录模型所在目录
            
            embedding_model = SentenceTransformer(
                model_abs_path, 
                device=device_name
            )
            model_name = model_abs_path
        else:
            # HuggingFace模型名：使用cache_folder
            logger.info(f"🌐 从HuggingFace加载: {model_path}")
            
            # 设置缓存目录
            if cache_folder:
                cache_path = Path(cache_folder)
                cache_path.mkdir(parents=True, exist_ok=True)
                os.environ['SENTENCE_TRANSFORMERS_HOME'] = str(cache_path)
                os.environ['TRANSFORMERS_CACHE'] = str(cache_path)
                cache_dir = str(cache_path)
                logger.info(f"📁 模型缓存目录: {cache_dir}")
            
            # 设置HuggingFace镜像
            if 'HF_ENDPOINT' not in os.environ:
                os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                logger.info("🌐 已设置HuggingFace镜像: https://hf-mirror.com")
            
            embedding_model = SentenceTransformer(
                model_path, 
                device=device_name,
                cache_folder=cache_folder
            )
            model_name = model_path
        
        device = device_name
        
        # 获取向量维度
        test_embedding = embedding_model.encode(["测试"], convert_to_numpy=True)
        dimension = test_embedding.shape[1]
        
        logger.success(f"✅ 模型加载完成: {model_name}")
        logger.success(f"✅ 向量维度: {dimension}")
        logger.success(f"✅ 运行设备: {device}")
        
    except Exception as e:
        logger.error(f"❌ 模型加载失败: {e}")
        raise


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    if embedding_model is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    return HealthResponse(
        status="healthy",
        model=model_name,
        dimension=dimension,
        device=device,
        cache_dir=cache_dir
    )


@app.post("/embeddings", response_model=EmbeddingResponse)
async def generate_embeddings(request: EmbeddingRequest):
    """生成文本embeddings"""
    if embedding_model is None:
        raise HTTPException(status_code=503, detail="模型未加载")
    
    try:
        logger.info(f"收到embedding请求: {len(request.texts)}个文本")
        
        # 验证文本
        if not request.texts:
            raise HTTPException(status_code=400, detail="文本列表不能为空")
        
        # 生成embeddings
        embeddings = embedding_model.encode(
            request.texts,
            batch_size=request.batch_size or DEFAULT_BATCH_SIZE,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        # 转换为列表
        embeddings_list = embeddings.tolist()
        
        logger.success(f"✅ 生成了{len(embeddings_list)}个embeddings")
        
        return EmbeddingResponse(
            embeddings=embeddings_list,
            model=model_name,
            dimension=dimension,
            count=len(embeddings_list)
        )
        
    except Exception as e:
        logger.error(f"❌ 生成embeddings失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成embeddings失败: {str(e)}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Embedding Service",
        "version": "1.0.0",
        "model": model_name,
        "dimension": dimension,
        "device": device,
        "cache_dir": cache_dir,
        "endpoints": {
            "health": "/health",
            "embeddings": "/embeddings",
            "docs": "/docs"
        }
    }


# ==================== 命令行启动 ====================

def main():
    """命令行启动"""
    parser = argparse.ArgumentParser(description="Embedding HTTP服务")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="服务host")
    parser.add_argument("--port", type=int, default=8080, help="服务端口")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help="模型名称或路径")
    parser.add_argument("--device", type=str, default=DEFAULT_DEVICE, help="运行设备 (cuda/cpu)")
    parser.add_argument("--cache-dir", type=str, default=None, help="模型缓存目录")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    parser.add_argument("--reload", action="store_true", help="开启热重载（开发模式）")
    
    args = parser.parse_args()
    
    # 初始化模型
    init_model(args.model, args.device, args.cache_dir)
    
    # 启动服务
    import uvicorn
    
    logger.info(f"🚀 启动Embedding服务: {args.host}:{args.port}")
    
    uvicorn.run(
        "embedding_server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()

