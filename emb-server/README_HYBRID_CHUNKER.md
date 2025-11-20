# HybridChunker HTTP 服务

混合分块器 HTTP 服务，提供多种文本分块策略。

## 功能特性

1. **多种分块策略**：
   - `character`: 基于字符数的固定大小分块（带重叠）
   - `sentence`: 基于句子的分块
   - `paragraph`: 基于段落的分块
   - `hierarchical`: 基于层次结构的分块（使用 HierarchicalChunker，适用于 Markdown 等结构化文档）
   - `hybrid`: 自动选择最佳策略（默认）

2. **HTTP API**：
   - POST `/chunks`: 输入文本，同步返回 chunks（JSON）
   - GET `/chunks/{chunk_id}`: 获取已保存的分块结果
   - GET `/chunks/{chunk_id}/download`: 下载分块文件（支持 JSON 和 TXT 格式）

3. **存储支持**：
   - 内存缓存（快速访问）
   - 文件存储（可选，用于持久化和下载）

## 安装依赖

确保已安装必要的依赖：

```bash
pip install fastapi uvicorn loguru
pip install docling  # 可选，用于层次化分块
```

## 启动服务

### 方式一：使用 Python 脚本

```bash
python emb-server/hybrid_chunker_server.py --host 0.0.0.0 --port 8081
```

### 方式二：使用 uvicorn

```bash
cd emb-server
uvicorn hybrid_chunker_server:app --host 0.0.0.0 --port 8081 --reload
```

### 命令行参数

```
--host: 服务host (默认: 0.0.0.0)
--port: 服务端口 (默认: 8081)
--chunk-size: 每块大小（字符数）(默认: 500)
--overlap: 重叠字符数 (默认: 50)
--strategy: 分块策略 (默认: hybrid)
--storage-dir: 存储目录 (默认: ./chunks_storage)
--workers: 工作进程数 (默认: 1)
--reload: 开启热重载（开发模式）
```

## API 使用示例

### 1. 健康检查

```bash
curl http://localhost:8081/health
```

响应：
```json
{
  "status": "healthy",
  "config": {
    "strategy": "hybrid",
    "chunk_size": 500,
    "overlap": 50
  },
  "storage_dir": "./chunks_storage"
}
```

### 2. 创建文本分块（同步返回）

```bash
curl -X POST http://localhost:8081/chunks \
  -H "Content-Type: application/json" \
  -d '{
    "text": "这是一段测试文本。\n\n这是第二段。\n\n这是第三段。",
    "chunk_size": 100,
    "overlap": 20,
    "strategy": "paragraph",
    "save_chunks": true
  }'
```

响应：
```json
{
  "chunk_id": "abc123...",
  "chunks": [
    {
      "text": "这是一段测试文本。",
      "index": 0,
      "start_char": 0,
      "end_char": 10,
      "metadata": {
        "chunk_size": 10,
        "strategy": "paragraph"
      }
    },
    ...
  ],
  "count": 3,
  "config": {
    "strategy": "paragraph",
    "chunk_size": 100,
    "overlap": 20
  },
  "download_url": "/chunks/abc123.../download"
}
```

### 3. 获取已保存的分块结果

```bash
curl http://localhost:8081/chunks/{chunk_id}
```

### 4. 下载分块文件（JSON 格式）

```bash
curl http://localhost:8081/chunks/{chunk_id}/download?format=json -o chunks.json
```

### 5. 下载分块文件（TXT 格式）

```bash
curl http://localhost:8081/chunks/{chunk_id}/download?format=txt -o chunks.txt
```

## Python 客户端示例

```python
import requests

# 创建分块
response = requests.post(
    "http://localhost:8081/chunks",
    json={
        "text": "这是一段很长的文本...",
        "chunk_size": 500,
        "overlap": 50,
        "strategy": "hybrid",
        "save_chunks": True,
        "metadata": {
            "document_id": "doc123",
            "title": "测试文档"
        }
    }
)

result = response.json()
print(f"生成了 {result['count']} 个 chunks")
print(f"Chunk ID: {result['chunk_id']}")

# 下载 JSON 文件
if result.get("download_url"):
    download_response = requests.get(
        f"http://localhost:8081{result['download_url']}?format=json"
    )
    with open("chunks.json", "wb") as f:
        f.write(download_response.content)
```

## 分块策略说明

### 1. Character（字符分块）

固定字符数分块，带重叠窗口。适用于任何文本。

```python
{
  "strategy": "character",
  "chunk_size": 500,
  "overlap": 50
}
```

### 2. Sentence（句子分块）

按句子分割，然后合并到合适的 chunk_size。尽量保留句子完整性。

```python
{
  "strategy": "sentence",
  "chunk_size": 500,
  "overlap": 50
}
```

### 3. Paragraph（段落分块）

按段落分割，尽量保留段落完整性。适用于有明确段落结构的文本。

```python
{
  "strategy": "paragraph",
  "chunk_size": 500,
  "overlap": 50
}
```

### 4. Hierarchical（层次化分块）

使用 HierarchicalChunker，适用于 Markdown 等有层次结构的文档。

```python
{
  "strategy": "hierarchical",
  "chunk_size": 500,
  "overlap": 50
}
```

### 5. Hybrid（混合策略，默认）

自动选择最佳策略：
1. 如果是 Markdown 且有层次结构，使用层次化分块
2. 否则使用段落分块
3. 对于超长内容，使用字符分块

```python
{
  "strategy": "hybrid",
  "chunk_size": 500,
  "overlap": 50
}
```

## 注意事项

1. **HierarchicalChunker 依赖**：`hierarchical` 和 `hybrid` 策略需要安装 `docling` 库。如果未安装，会自动回退到段落分块。

2. **存储目录**：如果设置了 `save_chunks: true`，chunks 会被保存到 `storage_dir` 目录。建议定期清理过期文件。

3. **内存缓存**：所有分块结果都会缓存在内存中，适合快速访问。重启服务后缓存会清空。

4. **文件下载**：下载的文件是临时生成的，下载完成后会自动删除。

## 与现有系统的集成

该服务可以独立运行，也可以与财报点评系统集成：

```python
from src.embeddings.http_embedding import HttpEmbeddingService

# 先使用 HybridChunker 服务进行分块
chunker_response = requests.post("http://localhost:8081/chunks", json={...})
chunks = chunker_response.json()["chunks"]

# 然后使用 Embedding 服务生成向量
embedding_service = HttpEmbeddingService(...)
embeddings = embedding_service.embed_texts([chunk["text"] for chunk in chunks])
```

## 性能建议

1. 对于大量文本，建议使用较大的 `chunk_size`（如 1000-2000）以减少 chunks 数量
2. 对于结构化文档（Markdown），使用 `hierarchical` 策略效果更好
3. 对于纯文本，使用 `paragraph` 或 `hybrid` 策略
4. 开发环境可以使用 `--reload` 参数开启热重载

