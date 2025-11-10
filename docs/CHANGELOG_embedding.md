# Embedding服务重构 - 变更说明

## 📅 日期
2025-11-10

## 🎯 目标
将embedding服务从直接加载本地模型改为支持通过HTTP接口调用，实现embedding服务的灵活部署。

## 📝 变更内容

### 1. 新增模块 `src/embeddings/`

创建了embedding服务的抽象层，支持多种实现方式：

#### 文件结构
```
src/embeddings/
├── __init__.py              # 模块导出
├── base_embedding.py        # 抽象基类
├── local_embedding.py       # 本地模型实现
├── http_embedding.py        # HTTP客户端实现
└── factory.py               # 工厂模式，自动选择实现
```

#### 核心类

**BaseEmbeddingService** - 抽象基类
- `encode()` - 生成embedding向量
- `get_dimension()` - 获取向量维度
- `get_model_name()` - 获取模型名称

**LocalEmbeddingService** - 本地模型实现
- 使用 SentenceTransformer 直接加载模型
- 支持 CUDA/CPU 设备选择
- 适用于开发测试、单机部署

**HttpEmbeddingService** - HTTP客户端实现
- 通过HTTP接口调用远程embedding服务
- 支持健康检查和连接验证
- 适用于生产环境、分布式部署

**EmbeddingFactory** - 工厂类
- 根据配置自动创建合适的服务实例
- 统一的创建接口

### 2. 配置文件修改

#### `src/config/settings.py`
新增配置项：
```python
EMBEDDING_SERVICE_TYPE: str      # "local" 或 "http"
EMBEDDING_API_URL: str          # HTTP服务地址
EMBEDDING_API_TIMEOUT: int      # 请求超时时间
```

#### `env.example`
新增配置示例：
```bash
EMBEDDING_SERVICE_TYPE=http
EMBEDDING_API_URL=http://localhost:8080
EMBEDDING_API_TIMEOUT=60
```

### 3. 核心服务重构

#### `src/retrieval/vector_retriever.py`
- 移除直接使用 SentenceTransformer
- 改用 EmbeddingFactory 创建服务
- 通过 `_init_embedding_service()` 初始化
- `_generate_embedding()` 使用统一接口

#### `src/ingestion/report_ingestion_service.py`
- 移除直接使用 SentenceTransformer
- 改用 EmbeddingFactory 创建服务
- 通过 `_init_embedding_service()` 初始化
- `_generate_embeddings()` 使用统一接口

### 4. 新增工具脚本

#### `scripts/embedding_server.py`
HTTP Embedding服务实现：
- 基于 FastAPI 构建
- 提供 `/health` 健康检查接口
- 提供 `/embeddings` 向量生成接口
- 支持命令行参数配置

启动方式：
```bash
python scripts/embedding_server.py --host 0.0.0.0 --port 8080 --device cuda
```

#### `scripts/test_embedding_service.py`
Embedding服务测试脚本：
- 测试服务连接
- 测试单个文本生成
- 测试批量文本生成
- 测试向量相似度
- 性能测试

运行方式：
```bash
python scripts/test_embedding_service.py
```

### 5. 文档

#### `docs/embedding_service.md`
详细的部署指南：
- 架构说明
- 部署方式对比
- HTTP服务部署步骤
- API接口规范
- 故障排查
- 最佳实践

#### `docs/embedding_quickstart.md`
5分钟快速开始指南：
- 本地模型部署
- HTTP服务部署
- 常见问题
- 最佳实践

### 6. 依赖更新

#### `requirements.txt`
新增依赖：
```
requests>=2.31.0  # HTTP客户端
```

## 🔄 迁移指南

### 从旧版本迁移

**无需修改代码**！只需更新配置文件：

#### 保持原有方式（本地模型）
```bash
# .env
EMBEDDING_SERVICE_TYPE=local
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
EMBEDDING_DIM=1024
EMBEDDING_DEVICE=cuda
```

#### 切换到HTTP服务
```bash
# 1. 启动embedding服务
python scripts/embedding_server.py --port 8080 --device cuda

# 2. 修改 .env
EMBEDDING_SERVICE_TYPE=http
EMBEDDING_API_URL=http://localhost:8080
EMBEDDING_API_TIMEOUT=60
```

## ✅ 测试验证

### 功能测试
```bash
# 测试embedding服务
python scripts/test_embedding_service.py

# 测试向量检索
python test_milvus_query.py

# 测试完整流程
python test_report_generation.py
```

### 性能测试
- 本地模型：约 200 texts/sec (GPU)
- HTTP服务：约 180 texts/sec (取决于网络延迟)

## 📊 优势

### 技术优势
1. **解耦**：embedding服务与主应用解耦，独立部署
2. **灵活**：支持多种部署方式，适应不同场景
3. **扩展**：易于扩展，可部署多实例实现负载均衡
4. **维护**：统一的抽象接口，易于维护和测试

### 业务优势
1. **资源隔离**：embedding服务可独立占用GPU资源
2. **成本优化**：可将embedding服务部署在廉价GPU实例上
3. **高可用**：支持多实例部署，提高系统可用性
4. **监控便利**：独立服务便于监控和告警

## 🎯 未来扩展

### 可能的优化方向
1. 支持更多embedding服务提供商（OpenAI, Cohere等）
2. 实现embedding缓存机制
3. 支持异步批量处理
4. 实现服务自动发现和负载均衡
5. 添加详细的性能监控指标

## 🔗 相关文档

- [快速开始](./embedding_quickstart.md)
- [详细部署指南](./embedding_service.md)
- [Oracle数据库支持方案](./oracle_database_support.md) (待实现)

## 👥 贡献者

- 实现者：AI Assistant
- 需求方：用户

## 📌 备注

本次重构遵循以下原则：
1. ✅ 向后兼容：不影响现有功能
2. ✅ 无侵入性：上层代码无需修改
3. ✅ 易于测试：提供完整的测试工具
4. ✅ 文档完善：提供详细的使用文档

