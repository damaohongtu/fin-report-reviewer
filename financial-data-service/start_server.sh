#!/bin/bash
# 启动财报数据服务 (Linux/Mac)

# 数据库配置（需要根据实际情况修改）
DATABASE_URL="postgresql://admin:password@localhost:5432/financial_reports"

echo "========================================"
echo "🚀 启动财报数据服务"
echo "========================================"
echo "服务端口: 8081"
echo "数据库: PostgreSQL"
echo "========================================"
echo ""

# 启动服务
python financial_data_server.py \
  --host 0.0.0.0 \
  --port 8081 \
  --database-url "$DATABASE_URL"

# 如果需要在后台运行：
# nohup python financial_data_server.py \
#   --host 0.0.0.0 \
#   --port 8081 \
#   --database-url "$DATABASE_URL" > financial_data_service.log 2>&1 &

