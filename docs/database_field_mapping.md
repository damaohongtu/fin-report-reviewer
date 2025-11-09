# 数据库字段映射说明

本文档记录 A 股财务报表数据库字段的正确命名和使用方法。

## 📋 表结构概览

### 1. 利润表 (a_share_income_statement)

| 字段名         | 中文名称                   | 说明                             | 代码中的别名          |
| -------------- | -------------------------- | -------------------------------- | --------------------- |
| `b001101000` | 营业收入                   | 企业经营过程中确认的营业收入     | `revenue`           |
| `b001201000` | 营业成本                   | 企业确认的营业成本               | `cost`              |
| `b001207000` | 税金及附加                 | 营业税、消费税、城市维护建设税等 | `business_tax`      |
| `b001209000` | 销售费用                   | 商品销售过程中发生的费用         | `sales_expense`     |
| `b001210000` | 管理费用                   | 组织和管理生产经营发生的费用     | `admin_expense`     |
| `b001216000` | 研发费用                   | 研究开发成本支出                 | `rd_expense`        |
| `b001211000` | 财务费用                   | 筹集资金发生的费用               | `finance_expense`   |
| `b001300000` | 营业利润                   | 与经营业务有关的利润             | `operating_profit`  |
| `b001000000` | 利润总额                   | 公司实现的利润总额               | `total_profit`      |
| `b002000000` | 净利润                     | 公司实现的净利润                 | `net_profit`        |
| `b002000101` | 归属于母公司所有者的净利润 | 合并报表净利润中归属于母公司部分 | `net_profit_parent` |

### 2. 资产负债表 (a_share_balance_sheet)

| 字段名         | 中文名称                   | 说明                                         | 代码中的别名                |
| -------------- | -------------------------- | -------------------------------------------- | --------------------------- |
| `a001100000` | 流动资产合计               | 流动资产各项目之合计                         | `current_assets`          |
| `a001200000` | 非流动资产合计             | 所有非流动资产的合计数                       | `non_current_assets`      |
| `a001000000` | 资产总计                   | 流动资产和非流动资产之合计                   | `total_assets`            |
| `a002100000` | 流动负债合计               | 流动负债各项目之合计                         | `current_liabilities`     |
| `a002200000` | 非流动负债合计             | 所有非流动负债的合计                         | `non_current_liabilities` |
| `a002000000` | 负债合计                   | 流动负债和非流动负债之合计                   | `total_liabilities`       |
| `a003000000` | 所有者权益合计             | 股东权益各项目之合计                         | `total_equity`            |
| `a003100000` | 归属于母公司所有者权益合计 | 合并报表中归属母公司所有者份额的权益         | `parent_equity`           |
| `a001123000` | 存货净额                   | 持有以备出售的产成品或商品、在产品、原材料等 | `inventory`               |
| `a002128000` | 合同负债                   | 已收或应收客户对价而应向客户转让商品的义务   | `contract_liability`      |

### 3. 现金流量表 (a_share_cashflow_statement)

**注意：表名是 `a_share_cashflow_statement`，不是 `a_share_cash_flow_statement`（没有下划线）**

| 字段名         | 中文名称                   | 说明                               | 代码中的别名                |
| -------------- | -------------------------- | ---------------------------------- | --------------------------- |
| `c001100000` | 经营活动现金流入小计       | 经营活动现金流入各项目合计         | `operating_cash_inflow`   |
| `c001200000` | 经营活动现金流出小计       | 经营活动现金流出各项目合计         | `operating_cash_outflow`  |
| `c001000000` | 经营活动产生的现金流量净额 | 经营活动现金流入减流出的差额       | `net_operating_cash_flow` |
| `c002100000` | 投资活动产生的现金流入小计 | 投资活动现金流入各项目合计         | `investing_cash_inflow`   |
| `c002200000` | 投资活动产生的现金流出小计 | 投资活动现金流出各项目合计         | `investing_cash_outflow`  |
| `c002000000` | 投资活动产生的现金流量净额 | 投资活动现金流入减流出的差额       | `net_investing_cash_flow` |
| `c003100000` | 筹资活动现金流入小计       | 筹资活动现金流入各项目合计         | `financing_cash_inflow`   |
| `c003200000` | 筹资活动现金流出小计       | 筹资活动现金流出各项目合计         | `financing_cash_outflow`  |
| `c003000000` | 筹资活动产生的现金流量净额 | 筹资活动现金流入减流出的差额       | `net_financing_cash_flow` |
| `c005000000` | 现金及现金等价物净增加额   | 会计期间内现金及现金等价物净增加额 | `net_cash_increase`       |

## 🔧 字段命名规则

### 前缀规则

- **利润表**: `b` 开头（如 `b001101000`）
- **资产负债表**: `a` 开头（如 `a001000000`）
- **现金流量表**: `c` 开头（如 `c001000000`）

### 编号规则

- **第一段 (001-009)**: 大类编号

  - 利润表：`b001` = 收入类, `b002` = 利润类
  - 资产负债表：`a001` = 资产类, `a002` = 负债类, `a003` = 权益类
  - 现金流量表：`c001` = 经营活动, `c002` = 投资活动, `c003` = 筹资活动
- **第二段 (100-900)**: 小类编号

  - 例如：`a001100000` = 流动资产合计, `a001200000` = 非流动资产合计
- **第三段 (000-999)**: 明细项目

  - 例如：`a001101000` = 货币资金（流动资产下的明细）

## 🔍 验证方法

### 1. SQL 验证

```sql
-- 验证表是否存在
SELECT table_name FROM information_schema.tables 
WHERE table_name IN ('a_share_income_statement', 'a_share_balance_sheet', 'a_share_cashflow_statement');

-- 验证字段是否存在
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'a_share_income_statement' 
  AND column_name IN ('b001101000', 'b001201000', 'b002000000');
```

### 2. Python 代码验证

```python
from src.database.financial_data_service import FinancialDataService

service = FinancialDataService()
data = service.get_income_statement(
    stock_code="601360",
    report_period="2024-03-31",
    report_type="A"
)
print(data)  # 检查是否成功返回数据
```

## 📚 参考资料

- 建表文件：`scripts/database_schema.sql`
- Wind 数据库字段说明文档
- A 股上市公司财务报表编制指南
