# Embedding服务快速开始

## 🚀 5分钟快速部署

### 步骤1：选择部署方式

#### 方式A：本地模型（推荐用于开发测试）

**优点**：简单快速，无需额外部署  
**缺点**：与主应用共享资源

```bash
# 1. 配置 .env
EMBEDDING_SERVICE_TYPE=local
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=1024
EMBEDDING_DEVICE=cuda  # 或 cpu
EMBEDDING_BATCH_SIZE=32

# 2. 直接启动主应用即可
python app.py
```

#### 方式B：HTTP服务（推荐用于生产环境）⭐

**优点**：资源隔离，易于扩展  
**缺点**：需要额外部署一个服务

```bash
# 1. 启动embedding服务（终端1）
python scripts/embedding_server.py --host 0.0.0.0 --port 8080 --device cuda

# 2. 配置 .env
EMBEDDING_SERVICE_TYPE=http
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=1024
EMBEDDING_API_URL=http://localhost:8080
EMBEDDING_API_TIMEOUT=60

# 3. 启动主应用（终端2）
python app.py
```

### 步骤2：测试服务

```bash
# 测试embedding功能
python scripts/test_embedding_service.py

# 如果使用HTTP服务，还可以直接测试API
curl http://localhost:8080/health
```

### 步骤3：使用服务

代码中无需修改，自动根据配置使用相应的embedding服务：

```python
from src.embeddings.factory import EmbeddingFactory

# 自动根据配置创建服务（local或http）
embedding_service = EmbeddingFactory.create_embedding_service()

# 生成单个文本的embedding
embedding = embedding_service.encode("测试文本")

# 批量生成
embeddings = embedding_service.encode(
    ["文本1", "文本2", "文本3"],
    batch_size=32
)
```

## 📊 两种方式对比

| 特性 | 本地模型 (local) | HTTP服务 (http) |
|-----|-----------------|----------------|
| **部署难度** | ⭐ 简单 | ⭐⭐ 需要额外服务 |
| **资源占用** | 与主应用共享GPU/内存 | 独立占用GPU/内存 |
| **扩展性** | ⭐ 单机 | ⭐⭐⭐ 可部署多实例 |
| **性能** | ⭐⭐⭐ 无网络开销 | ⭐⭐ 有网络开销 |
| **适用场景** | 开发、测试、单机部署 | 生产、分布式部署 |

## 🔧 常见问题

### Q1: 如何切换embedding方式？

修改 `.env` 文件中的 `EMBEDDING_SERVICE_TYPE`：
- `local` - 本地模型
- `http` - HTTP服务

重启应用即可，无需修改代码。

### Q2: HTTP服务启动失败怎么办？

检查：
1. 端口是否被占用：`netstat -ano | findstr 8080`
2. GPU是否可用：`nvidia-smi`
3. 依赖是否安装：`pip install fastapi uvicorn sentence-transformers`

### Q3: 如何使用不同的模型？

修改 `.env` 中的 `EMBEDDING_MODEL`：
```bash
# 使用更小的模型（更快，但精度稍低）
EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5
EMBEDDING_DIM=768

# 使用本地模型路径
EMBEDDING_MODEL=/path/to/your/model
EMBEDDING_DIM=1024
```

### Q4: 如何提高性能？

**本地模型方式**：
- 使用GPU：`EMBEDDING_DEVICE=cuda`
- 增加批处理大小：`EMBEDDING_BATCH_SIZE=64`

**HTTP服务方式**：
- 部署在GPU服务器上
- 部署多个实例，使用Nginx负载均衡
- 调整timeout：`EMBEDDING_API_TIMEOUT=120`

### Q5: 生产环境推荐配置？

```bash
# 推荐配置
EMBEDDING_SERVICE_TYPE=http
EMBEDDING_API_URL=http://embedding-server:8080
EMBEDDING_API_TIMEOUT=60
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=1024
```

单独部署embedding服务：
```bash
# 在GPU服务器上
python scripts/embedding_server.py \
  --host 0.0.0.0 \
  --port 8080 \
  --device cuda \
  --model BAAI/bge-large-zh-v1.5
```

## 🎯 最佳实践

1. **开发阶段**：使用 `local` 模式，快速迭代
2. **测试阶段**：使用 `http` 模式，模拟生产环境
3. **生产阶段**：使用 `http` 模式，独立部署在GPU服务器
4. **监控告警**：监控embedding服务的响应时间和可用性
5. **备份方案**：准备多个embedding服务实例，实现高可用

## 📚 更多文档

- [详细部署指南](./embedding_service.md)
- [API接口文档](http://localhost:8080/docs)（启动服务后访问）
- [架构设计说明](./embedding_service.md#架构说明)

## 💡 示例代码

完整的测试示例见：`scripts/test_embedding_service.py`

```bash
# 运行测试
python scripts/test_embedding_service.py
```

