# 财报点评系统

> 基于 LangChain + DeepSeek + PostgreSQL + Milvus 的智能财报分析系统

## 🎯 核心理念

### 数据与逻辑分离

1. **结构化数据处理**：从PostgreSQL获取财报三表数据，使用代码逻辑计算客观技术指标
2. **非结构化数据处理**：从Milvus向量库检索财报文本，提供业务上下文
3. **AI智能分析**：结合结构化指标和非结构化上下文，由LLM生成专业报告

### 设计原则

- ✅ **避免GIGO**：能够提前计算的指标使用代码逻辑，避免LLM计算错误
- ✅ **行业可扩展**：基于行业配置定义核心、辅助和个性化指标
- ✅ **提示词独立**：所有Prompt集中管理，便于修改
- ✅ **数据源可扩展**：预留接口支持公告等其他数据源
- ✅ **单一职责**：每个模块职责明确，便于维护和扩展

## 📂 项目结构

```
fin-report-reviewer/
├── src/
│   ├── config/                         # 配置模块
│   │   ├── settings.py                # 环境配置（数据库、LLM、Embedding等）
│   │   ├── industry_configs.py        # 行业配置（核心/辅助/个性化指标）
│   │   └── prompts.py                 # 提示词配置（集中管理所有Prompt）
│   ├── database/                       # 数据库服务
│   │   └── financial_data_service.py  # PostgreSQL财务数据服务
│   ├── retrieval/                      # 向量检索
│   │   └── vector_retriever.py        # Milvus检索服务
│   ├── extractors/                     # 指标提取
│   │   └── indicator_extractor.py     # 技术指标计算器（客观计算）
│   ├── analysis/                       # 分析生成
│   │   └── report_generator.py        # 报告生成器（协调所有模块）
│   ├── ingestion/                      # 数据摄入
│   │   └── report_ingestion_service.py # PDF摄入Milvus（单一职责）
│   └── parsers/                        # 数据解析
│       └── financial_pdf_parser.py    # PDF文本解析器
├── scripts/
│   ├── database_schema.sql            # 数据库表结构（Wind格式）
│   └── import_financial_data.py       # 财报数据导入脚本
├── docs/
│   ├── 需求文档.md                    # 业务需求与行业特征
│   └── 系统架构设计.md                # 系统架构详细设计
├── data/
│   ├── pdfs/                          # PDF财报文件
│   └── reports/                       # 生成的报告
├── generate_report.py                 # 主程序入口
├── test_report_generation.py          # 完整功能测试
├── test_milvus_query.py              # Milvus查询测试
├── test_report_ingestion.py          # PDF摄入测试
└── requirements.txt                   # Python依赖
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp env.example .env
# 编辑 .env 文件，配置以下必需项：
# - DEEPSEEK_API_KEY
# - DATABASE_URL
# - MILVUS_HOST、MILVUS_USER、MILVUS_PASSWORD
# - EMBEDDING_MODEL (本地模型路径或HuggingFace模型名)
```

### 2. 数据准备

#### 2.1 创建数据库表

```bash
# 使用scripts/database_schema.sql创建表结构
psql -U postgres -d financial_reports -f scripts/database_schema.sql
```

#### 2.2 摄入PDF到Milvus（可选）

```bash
python -m src.ingestion.report_ingestion_service \
  --file data/pdfs/360-2024Q1.pdf \
  --company "三六零" \
  --code "601360" \
  --period "2024-03-31"
```

### 3. 生成报告

```bash
python generate_report.py \
  --company "三六零" \
  --code "601360" \
  --period "2024-03-31" \
  --industry "computer"
```

### 4. 测试功能

```bash
# 测试完整流程
python test_report_generation.py

# 测试Milvus查询
python test_milvus_query.py
```

## 📊 支持的行业

当前支持：

- **计算机行业** (`computer`)
  - 核心指标：营业收入增速、净利润增速
  - 辅助指标：毛利率、研发费用率、销售费用率
  - 个性化指标：合同负债、存货

扩展新行业：

1. 在 `src/config/industry_configs.py` 中定义行业配置
2. 在 `src/config/prompts.py` 中添加行业提示词（可选）
3. 注册到 `IndustryConfigManager`

## 🔧 配置说明

### 环境变量（.env）

```ini
# LLM配置
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/financial_reports

# Milvus配置
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=username
MILVUS_PASSWORD=password
MILVUS_COLLECTION_NAME=financial_reports

# Embedding模型配置
EMBEDDING_MODEL=BAAI/bge-base-zh-v1.5  # 或本地路径
EMBEDDING_DIM=768
EMBEDDING_DEVICE=cpu
```

### 行业配置示例

```python
# src/config/industry_configs.py
COMPUTER_INDUSTRY_CONFIG = IndustryConfig(
    code="computer",
    name="计算机",
    description="...",
    characteristics=[...],
    indicators=[
        IndicatorConfig(
            name="revenue_growth",
            display_name="营业收入增速",
            priority=IndicatorPriority.CORE,
            ...
        ),
        ...
    ]
)
```

## 🛠️ 开发指南

### 添加新的指标

1. 在 `industry_configs.py` 中定义指标配置
2. 在 `indicator_extractor.py` 中实现计算逻辑
3. 在 `prompts.py` 中更新分析提示词

### 添加新的数据源

1. 在 `src/database/` 创建新的服务类
2. 在 `report_generator.py` 中集成新数据源
3. 更新提示词以利用新数据

## 📝 使用场景

### 场景1：批量生成季报点评

```bash
# 循环生成多家公司的季报
for code in 601360 000001 600000; do
  python generate_report.py \
    --company "公司名" \
    --code "$code" \
    --period "2024-03-31" \
    --industry "computer"
done
```

### 场景2：对比分析

```bash
# 生成同一公司不同期的报告，手动对比
python generate_report.py --company "三六零" --code "601360" --period "2024-03-31" --industry "computer"
python generate_report.py --company "三六零" --code "601360" --period "2023-12-31" --industry "computer"
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

如有问题，请提交Issue或联系开发团队。

---

*本系统旨在辅助财报分析，生成的报告仅供参考，不构成投资建议。*
