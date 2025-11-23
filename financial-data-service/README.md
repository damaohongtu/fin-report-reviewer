# 财报数据HTTP服务

将PostgreSQL数据库的财报数据查询封装为独立的HTTP服务，实现数据访问层与应用层的解耦。

## 📋 功能特性

- ✅ RESTful API 接口
- ✅ 支持三张财报表（利润表、资产负债表、现金流量表）
- ✅ 支持历史期查询
- ✅ 支持完整数据一次性获取
- ✅ 健康检查接口
- ✅ FastAPI 自动生成API文档

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary loguru
```

### 2. 配置数据库

修改启动脚本中的数据库连接字符串：

```bash
# PostgreSQL
DATABASE_URL="postgresql://user:password@localhost:5432/financial_reports"
```

### 3. 启动服务

**Linux/Mac:**
```bash
cd financial-data-service
chmod +x start_server.sh
./start_server.sh
```

**Windows:**
```cmd
cd financial-data-service
start_server.bat
```

**或直接命令行:**
```bash
python financial_data_server.py \
  --host 0.0.0.0 \
  --port 8081 \
  --database-url "postgresql://user:password@localhost:5432/financial_reports"
```

### 4. 验证服务

```bash
# 健康检查
curl http://localhost:8081/health

# 查看API文档
打开浏览器: http://localhost:8081/docs
```

## 📖 API 文档

### 主要端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/api/income-statement` | POST | 查询利润表 |
| `/api/balance-sheet` | POST | 查询资产负债表 |
| `/api/cash-flow` | POST | 查询现金流量表 |
| `/api/historical-periods` | POST | 查询历史期 |
| `/api/complete-data` | POST | 查询完整财务数据 |
| `/docs` | GET | Swagger API文档 |

### 使用示例

#### 1. 查询利润表

```bash
curl -X POST http://localhost:8081/api/income-statement \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "report_period": "2024-03-31",
    "report_type": "A"
  }'
```

#### 2. 查询完整财务数据

```bash
curl -X POST http://localhost:8081/api/complete-data \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "report_period": "2024-03-31",
    "report_type": "A",
    "include_previous": true
  }'
```

#### 3. Python 客户端

```python
import requests

# 查询利润表
response = requests.post(
    "http://localhost:8081/api/income-statement",
    json={
        "stock_code": "000001",
        "report_period": "2024-03-31",
        "report_type": "A"
    }
)

result = response.json()
if result["success"]:
    data = result["data"]
    print(f"营业收入: {data['revenue']}")
    print(f"净利润: {data['net_profit']}")
```

## 🏗️ 架构说明

```
主应用 (fin-report-reviewer)
    ↓ HTTP请求
财报数据服务 (financial-data-service:8081)
    ↓ SQL查询
PostgreSQL 数据库
```

## ⚙️ 配置参数

| 参数 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `--host` | 服务地址 | 0.0.0.0 | 否 |
| `--port` | 服务端口 | 8081 | 否 |
| `--database-url` | 数据库连接URL | - | **是** |
| `--reload` | 热重载（开发模式） | False | 否 |

## 🔍 故障排查

### 1. 端口被占用

```bash
# Linux/Mac
lsof -i :8081
kill -9 <PID>

# Windows
netstat -ano | findstr :8081
taskkill /PID <PID> /F
```

### 2. 数据库连接失败

检查：
- 数据库URL是否正确
- 数据库服务是否启动
- 网络连接是否正常
- 数据库用户权限

### 3. 503 Service Unavailable

确保数据库已连接。查看启动日志：
```
✅ 数据库连接成功
```

## 📊 性能考虑

- 使用连接池管理数据库连接
- 支持并发请求
- 自动处理连接健康检查
- 1小时自动回收连接

## 🔗 相关服务

系统包含三个独立服务：

1. **财报数据服务** (8081) - 本服务
2. **Embedding服务** (8080) - 文本向量化
3. **主应用** - 财报点评系统

## 📝 注意事项

1. ⚠️ 数据库URL包含密码，请妥善保管
2. ⚠️ 生产环境建议使用环境变量传递敏感信息
3. ⚠️ 建议配置防火墙规则限制访问
4. ✅ 服务间通信建议使用内网地址

## 🎯 最佳实践

1. **开发环境**: 本地启动，使用 `--reload`
2. **生产环境**: Docker容器化部署
3. **监控**: 定期检查 `/health` 端点
4. **日志**: 使用日志聚合工具
5. **备份**: 定期备份数据库

