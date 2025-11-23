# Embedding服务部署指南

## 概述

系统支持两种Embedding服务部署方式：

1. **本地模型方式** (`EMBEDDING_SERVICE_TYPE=local`)：直接加载SentenceTransformer模型
2. **HTTP服务方式** (`EMBEDDING_SERVICE_TYPE=http`)：通过HTTP接口调用独立的embedding服务

## 架构说明

```
财报点评系统
    ↓
EmbeddingFactory
    ↓
BaseEmbeddingService (抽象接口)
    ↓
    ├── LocalEmbeddingService (本地模型)
    └── HttpEmbeddingService (HTTP客户端)
            ↓
        HTTP Embedding Server (独立服务)
```

## HTTP服务方式的优势

1. **资源隔离**：Embedding服务独立部署，避免与主应用竞争资源
2. **易于扩展**：可以部署多个embedding服务实例，实现负载均衡
3. **灵活部署**：可以使用GPU服务器专门运行embedding服务
4. **统一管理**：多个应用可以共享同一个embedding服务

## 配置方式

### 1. 本地模型方式

适用场景：单机部署、快速开发测试

```bash
# .env 配置
EMBEDDING_SERVICE_TYPE=local
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=1024
EMBEDDING_DEVICE=cuda
EMBEDDING_BATCH_SIZE=32
```

### 2. HTTP服务方式 ⭐ (推荐)

适用场景：生产环境、分布式部署

```bash
# .env 配置
EMBEDDING_SERVICE_TYPE=http
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=1024
EMBEDDING_API_URL=http://localhost:8080
EMBEDDING_API_TIMEOUT=60
```

## HTTP Embedding服务部署

### 方式一：使用提供的FastAPI服务

#### 1. 安装依赖

```bash
pip install fastapi uvicorn sentence-transformers torch
```

#### 2. 启动服务

```bash
# 启动embedding服务（默认端口8080）
python scripts/embedding_server.py --host 0.0.0.0 --port 8080 --device cuda

# 或使用uvicorn直接启动
uvicorn scripts.embedding_server:app --host 0.0.0.0 --port 8080
```

#### 3. 验证服务

```bash
# 健康检查
curl http://localhost:8080/health

# 测试embedding生成
curl -X POST http://localhost:8080/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "texts": ["测试文本"],
    "model": "BAAI/bge-large-zh-v1.5"
  }'
```

### 方式二：Docker部署

```bash
# 构建镜像
docker build -t embedding-service -f docker/Dockerfile.embedding .

# 运行容器
docker run -d \
  --name embedding-service \
  --gpus all \
  -p 8080:8080 \
  -e MODEL_NAME=BAAI/bge-large-zh-v1.5 \
  -e DEVICE=cuda \
  embedding-service
```

### 方式三：使用现有的Embedding服务

如果你已经有现成的embedding服务，只需确保它提供以下API接口：

#### API规范

**健康检查** `GET /health`

```json
{
  "status": "healthy",
  "model": "BAAI/bge-large-zh-v1.5",
  "dimension": 1024
}
```

**生成Embedding** `POST /embeddings`

请求：
```json
{
  "texts": ["文本1", "文本2"],
  "model": "BAAI/bge-large-zh-v1.5",
  "batch_size": 32
}
```

响应：
```json
{
  "embeddings": [
    [0.123, 0.456, ...],  // 1024维向量
    [0.789, 0.012, ...]
  ],
  "model": "BAAI/bge-large-zh-v1.5",
  "dimension": 1024,
  "count": 2
}
```

## 性能对比

| 方式 | 优点 | 缺点 | 适用场景 |
|-----|------|------|---------|
| **本地模型** | 无网络开销、简单 | 与主应用竞争资源 | 开发测试 |
| **HTTP服务** | 资源隔离、易扩展 | 网络开销、需要额外部署 | 生产环境 |

## 故障排查

### 1. HTTP服务连接失败

```python
# 检查服务是否启动
curl http://localhost:8080/health

# 检查防火墙设置
# 确保端口8080已开放

# 查看服务日志
# 检查embedding server的日志输出
```

### 2. 请求超时

增加超时时间：
```bash
EMBEDDING_API_TIMEOUT=120  # 增加到120秒
```

### 3. 内存不足

- 降低batch_size
- 使用更小的模型（bge-base-zh-v1.5）
- 使用CPU模式

## 最佳实践

1. **生产环境推荐**：使用HTTP服务方式，独立部署在GPU服务器上
2. **批量处理**：尽量使用批量接口，提高吞吐量
3. **连接池**：HTTP客户端使用连接池，减少连接开销
4. **监控告警**：监控embedding服务的响应时间和错误率
5. **容灾备份**：部署多个embedding服务实例，实现高可用

## 扩展：负载均衡

如果需要更高的性能，可以部署多个embedding服务实例：

```nginx
# Nginx配置示例
upstream embedding_service {
    server 192.168.1.101:8080;
    server 192.168.1.102:8080;
    server 192.168.1.103:8080;
}

server {
    listen 80;
    location / {
        proxy_pass http://embedding_service;
    }
}
```

然后配置：
```bash
EMBEDDING_API_URL=http://your-nginx-server
```

