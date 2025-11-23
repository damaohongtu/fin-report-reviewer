"""
混合分块器 HTTP 服务

提供HTTP接口的分块服务，供财报点评系统调用
使用 FastAPI + HybridChunker 实现

启动方式：
python emb-server/hybrid_chunker_server.py --host 0.0.0.0 --port 8081

或使用uvicorn：
uvicorn hybrid_chunker_server:app --host 0.0.0.0 --port 8081 --reload

参数说明：
--host: 服务host (默认: 0.0.0.0)
--port: 服务端口 (默认: 8081)
--chunk-size: 每块大小 (默认: 500)
--overlap: 重叠字符数 (默认: 50)
--strategy: 分块策略 (默认: hybrid)
--storage-dir: 存储目录 (默认: ./chunks_storage)
"""

import argparse
import os
import json
import hashlib
import time
from typing import List, Optional, Dict
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from loguru import logger

from hybrid_chunker import HybridChunker, ChunkConfig

# ==================== 配置 ====================
DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 50
DEFAULT_STRATEGY = "hybrid"
DEFAULT_STORAGE_DIR = "./chunks_storage"

# ==================== API模型 ====================

class ChunkRequest(BaseModel):
    """分块请求"""
    text: str = Field(..., description="输入文本", min_length=1)
    chunk_size: Optional[int] = Field(default=None, description="每块大小（字符数）", ge=50, le=5000)
    overlap: Optional[int] = Field(default=None, description="重叠字符数", ge=0, le=200)
    strategy: Optional[str] = Field(default=None, description="分块策略: character/sentence/paragraph/hierarchical/hybrid")
    metadata: Optional[Dict] = Field(default=None, description="元数据（如文档ID、标题等）")
    save_chunks: Optional[bool] = Field(default=False, description="是否保存chunks以便下载")

class ChunkResponse(BaseModel):
    """分块响应"""
    chunk_id: str = Field(..., description="本次分块的唯一ID")
    chunks: List[Dict] = Field(..., description="分块列表")
    count: int = Field(..., description="分块数量")
    config: Dict = Field(..., description="使用的配置")
    download_url: Optional[str] = Field(None, description="下载URL（如果save_chunks=True）")

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    config: Dict = Field(..., description="当前配置")
    storage_dir: Optional[str] = Field(None, description="存储目录")

# ==================== FastAPI应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # Startup: 初始化存储目录
    logger.info("🚀 HybridChunker 服务启动中...")
    storage_dir = app.state.storage_dir
    if storage_dir:
        Path(storage_dir).mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 存储目录: {storage_dir}")
    
    # 清理过期文件（可选）
    # _cleanup_old_chunks(storage_dir, days=7)
    
    yield
    
    # Shutdown: 清理资源（如果需要）
    logger.info("🛑 HybridChunker 服务关闭中...")

app = FastAPI(
    title="HybridChunker Service",
    description="提供混合策略文本分块服务",
    version="1.0.0",
    lifespan=lifespan
)

# 全局变量
chunker: Optional[HybridChunker] = None
chunk_config: Optional[ChunkConfig] = None
storage_dir: Optional[str] = None

# 内存存储（用于快速访问）
chunks_cache: Dict[str, Dict] = {}


def init_chunker(config: ChunkConfig, storage_path: Optional[str] = None):
    """初始化分块器"""
    global chunker, chunk_config, storage_dir
    
    chunk_config = config
    storage_dir = storage_path or DEFAULT_STORAGE_DIR
    app.state.storage_dir = storage_dir
    
    try:
        chunker = HybridChunker(config)
        logger.success(f"✅ HybridChunker 初始化完成")
        logger.info(f"   策略: {config.strategy}")
        logger.info(f"   块大小: {config.chunk_size}")
        logger.info(f"   重叠: {config.overlap}")
    except Exception as e:
        logger.error(f"❌ HybridChunker 初始化失败: {e}")
        raise


def _save_chunks_to_file(chunk_id: str, chunks: List[Dict], metadata: Optional[Dict] = None) -> str:
    """保存chunks到文件
    
    Returns:
        文件路径
    """
    if not storage_dir:
        raise ValueError("存储目录未设置")
    
    # 创建存储目录
    Path(storage_dir).mkdir(parents=True, exist_ok=True)
    
    # 文件路径
    file_path = Path(storage_dir) / f"{chunk_id}.json"
    
    # 保存数据
    data = {
        "chunk_id": chunk_id,
        "created_at": time.time(),
        "metadata": metadata or {},
        "chunks": chunks
    }
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 已保存chunks到文件: {file_path}")
    return str(file_path)


def _load_chunks_from_file(chunk_id: str) -> Optional[Dict]:
    """从文件加载chunks"""
    if not storage_dir:
        return None
    
    file_path = Path(storage_dir) / f"{chunk_id}.json"
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ 加载chunks文件失败: {e}")
        return None


def _generate_chunk_id(text: str, config: ChunkConfig) -> str:
    """生成唯一的chunk_id"""
    # 基于文本内容和配置生成ID
    content = f"{text[:100]}_{config.chunk_size}_{config.overlap}_{config.strategy}_{time.time()}"
    return hashlib.md5(content.encode()).hexdigest()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查"""
    if chunker is None:
        raise HTTPException(status_code=503, detail="分块器未初始化")
    
    return HealthResponse(
        status="healthy",
        config={
            "strategy": chunk_config.strategy,
            "chunk_size": chunk_config.chunk_size,
            "overlap": chunk_config.overlap
        },
        storage_dir=storage_dir
    )


@app.post("/chunks", response_model=ChunkResponse)
async def create_chunks(request: ChunkRequest):
    """创建文本分块"""
    if chunker is None:
        raise HTTPException(status_code=503, detail="分块器未初始化")
    
    try:
        logger.info(f"收到分块请求: 文本长度={len(request.text)}, 策略={request.strategy or 'default'}")
        
        # 验证文本
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="文本不能为空")
        
        # 使用请求中的配置或默认配置
        config = ChunkConfig(
            chunk_size=request.chunk_size or chunk_config.chunk_size,
            overlap=request.overlap if request.overlap is not None else chunk_config.overlap,
            strategy=request.strategy or chunk_config.strategy,
            min_chunk_size=chunk_config.min_chunk_size,
            max_chunk_size=chunk_config.max_chunk_size,
            preserve_boundaries=chunk_config.preserve_boundaries
        )
        
        # 创建临时chunker（如果配置不同）
        if (config.chunk_size != chunk_config.chunk_size or 
            config.overlap != chunk_config.overlap or 
            config.strategy != chunk_config.strategy):
            temp_chunker = HybridChunker(config)
            chunks = temp_chunker.chunk(request.text, metadata=request.metadata)
        else:
            chunks = chunker.chunk(request.text, metadata=request.metadata)
        
        # 生成chunk_id
        chunk_id = _generate_chunk_id(request.text, config)
        
        # 保存到缓存
        chunks_cache[chunk_id] = {
            "chunks": chunks,
            "config": {
                "strategy": config.strategy,
                "chunk_size": config.chunk_size,
                "overlap": config.overlap
            },
            "metadata": request.metadata or {}
        }
        
        # 如果请求保存，则保存到文件
        download_url = None
        if request.save_chunks:
            _save_chunks_to_file(chunk_id, chunks, request.metadata)
            download_url = f"/chunks/{chunk_id}/download"
        
        logger.success(f"✅ 文本分块完成: {len(chunks)}个chunks, chunk_id={chunk_id}")
        
        return ChunkResponse(
            chunk_id=chunk_id,
            chunks=chunks,
            count=len(chunks),
            config={
                "strategy": config.strategy,
                "chunk_size": config.chunk_size,
                "overlap": config.overlap
            },
            download_url=download_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 文本分块失败: {e}")
        raise HTTPException(status_code=500, detail=f"文本分块失败: {str(e)}")


@app.get("/chunks/{chunk_id}")
async def get_chunks(chunk_id: str):
    """获取分块结果（通过chunk_id）"""
    # 先从缓存查找
    if chunk_id in chunks_cache:
        return JSONResponse(content=chunks_cache[chunk_id])
    
    # 从文件加载
    data = _load_chunks_from_file(chunk_id)
    if data:
        return JSONResponse(content=data)
    
    raise HTTPException(status_code=404, detail=f"未找到chunk_id: {chunk_id}")


@app.get("/chunks/{chunk_id}/download")
async def download_chunks(
    chunk_id: str,
    background_tasks: BackgroundTasks,
    format: str = Query(default="json", description="下载格式: json/txt", regex="^(json|txt)$")
):
    """下载分块文件"""
    # 获取chunks数据
    data = None
    
    # 先从缓存查找
    if chunk_id in chunks_cache:
        cache_data = chunks_cache[chunk_id]
        data = {
            "chunk_id": chunk_id,
            "created_at": time.time(),
            "metadata": cache_data.get("metadata", {}),
            "chunks": cache_data.get("chunks", [])
        }
    else:
        # 从文件加载
        data = _load_chunks_from_file(chunk_id)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"未找到chunk_id: {chunk_id}")
    
    # 根据格式生成文件
    if format == "json":
        # 生成临时JSON文件
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8')
        json.dump(data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        
        # 添加到后台任务：下载后删除文件
        background_tasks.add_task(lambda: Path(temp_file.name).unlink(missing_ok=True))
        
        return FileResponse(
            temp_file.name,
            media_type="application/json",
            filename=f"chunks_{chunk_id}.json"
        )
    elif format == "txt":
        # 生成TXT文件
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        
        # 写入TXT格式
        temp_file.write(f"Chunk ID: {chunk_id}\n")
        temp_file.write(f"Created At: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data.get('created_at', time.time())))}\n")
        temp_file.write(f"Total Chunks: {len(data.get('chunks', []))}\n")
        temp_file.write("=" * 80 + "\n\n")
        
        for idx, chunk in enumerate(data.get("chunks", []), 1):
            temp_file.write(f"[Chunk {idx}]\n")
            temp_file.write(f"Index: {chunk.get('index', idx-1)}\n")
            temp_file.write(f"Length: {len(chunk.get('text', ''))} chars\n")
            temp_file.write("-" * 80 + "\n")
            temp_file.write(chunk.get("text", "") + "\n")
            temp_file.write("=" * 80 + "\n\n")
        
        temp_file.close()
        
        # 添加到后台任务：下载后删除文件
        background_tasks.add_task(lambda: Path(temp_file.name).unlink(missing_ok=True))
        
        return FileResponse(
            temp_file.name,
            media_type="text/plain",
            filename=f"chunks_{chunk_id}.txt"
        )
    else:
        raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "HybridChunker Service",
        "version": "1.0.0",
        "config": {
            "strategy": chunk_config.strategy if chunk_config else "unknown",
            "chunk_size": chunk_config.chunk_size if chunk_config else 0,
            "overlap": chunk_config.overlap if chunk_config else 0
        },
        "storage_dir": storage_dir,
        "endpoints": {
            "health": "/health",
            "create_chunks": "POST /chunks",
            "get_chunks": "GET /chunks/{chunk_id}",
            "download_chunks": "GET /chunks/{chunk_id}/download?format=json|txt",
            "docs": "/docs"
        }
    }


# ==================== 命令行启动 ====================

def main():
    """命令行启动"""
    parser = argparse.ArgumentParser(description="HybridChunker HTTP服务")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="服务host")
    parser.add_argument("--port", type=int, default=8081, help="服务端口")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help="每块大小（字符数）")
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP, help="重叠字符数")
    parser.add_argument("--strategy", type=str, default=DEFAULT_STRATEGY, 
                        choices=["character", "sentence", "paragraph", "hierarchical", "hybrid"],
                        help="分块策略")
    parser.add_argument("--storage-dir", type=str, default=DEFAULT_STORAGE_DIR, help="存储目录")
    parser.add_argument("--workers", type=int, default=1, help="工作进程数")
    parser.add_argument("--reload", action="store_true", help="开启热重载（开发模式）")
    
    args = parser.parse_args()
    
    # 初始化配置
    config = ChunkConfig(
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        strategy=args.strategy
    )
    
    # 初始化分块器
    init_chunker(config, args.storage_dir)
    
    # 启动服务
    import uvicorn
    
    logger.info(f"🚀 启动 HybridChunker 服务: {args.host}:{args.port}")
    
    uvicorn.run(
        "hybrid_chunker_server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info"
    )


if __name__ == "__main__":
    main()

