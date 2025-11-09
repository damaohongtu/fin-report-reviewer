# 财报点评系统 - LangGraph 架构说明

## 📐 架构概览

基于 **LangChain + LangGraph + PostgreSQL + Milvus + DeepSeek** 技术栈实现的智能财报分析系统。

### 核心设计理念

1. **职责分离**
   - **Tools**：执行具体任务（数据获取、指标计算）
   - **Nodes**：处理业务逻辑
   - **Graphs**：编排工作流
   - **LLM**：分析和生成洞察

2. **避免GIGO**
   - 所有数值计算由代码精确完成（Tools）
   - LLM 仅用于分析和报告生成

3. **状态管理**
   - 使用 LangGraph State 在节点间传递数据
   - 状态包含：数据、指标、分析结果、元数据等

---

## 🏗️ 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层                                │
│              generate_report.py                          │
│              ReportGenerator                             │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────┐
│                LangGraph 编排层                          │
│        src/graphs/financial_report_graph.py             │
│              (只负责定义工作流DAG)                       │
│                                                          │
│  fetch_data → calculate → retrieve → analyze_core →     │
│  analyze_aux → analyze_specific → generate → quality    │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────┐
│                   节点层 (Nodes)                         │
│               src/nodes/*.py                             │
│        (独立的处理单元，调用Tools/LLM)                  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ data_nodes   │  │ calculation  │  │ analysis     │ │
│  │ - 数据获取   │  │ _nodes       │  │ _nodes       │ │
│  │ - Milvus检索 │  │ - 指标计算   │  │ - LLM分析    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐                                       │
│  │ report_nodes │                                       │
│  │ - 报告生成   │                                       │
│  │ - 质量检查   │                                       │
│  └──────────────┘                                       │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────┐
│                   工具层 (Tools)                         │
│                 src/tools/*.py                           │
│            (封装为 LangChain Tools)                     │
│                                                          │
│  ┌──────────────────┐  ┌──────────────────┐           │
│  │ 数据获取 Tools   │  │ 指标计算 Tools   │           │
│  │ - get_income     │  │ - calc_revenue   │           │
│  │ - get_balance    │  │ - calc_margin    │           │
│  │ - get_cashflow   │  │ - calc_rd_ratio  │           │
│  │ - get_complete   │  │ - calc_all       │           │
│  └──────────────────┘  └──────────────────┘           │
│                                                          │
│  ┌──────────────────┐                                   │
│  │ Milvus Tools     │                                   │
│  │ - retrieve_by    │                                   │
│  │ - get_context    │                                   │
│  └──────────────────┘                                   │
└──────────────────┬──────────────────────────────────────┘
                   ↓
┌─────────────────────────────────────────────────────────┐
│                   数据层                                 │
│                                                          │
│  ┌──────────────┐           ┌──────────────┐           │
│  │ PostgreSQL   │           │   Milvus     │           │
│  │ 财报三表     │           │   文本向量   │           │
│  └──────────────┘           └──────────────┘           │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 工作流说明

### LangGraph 工作流 DAG

```
┌──────────────────┐
│ fetch_financial  │  数据获取节点
│      _data       │  调用Tool获取财报三表
└────────┬─────────┘
         ↓
┌──────────────────┐
│   calculate      │  指标计算节点
│   _indicators    │  调用Tool计算所有指标（代码计算）
└────────┬─────────┘
         ↓
┌──────────────────┐
│   retrieve       │  上下文检索节点
│   _context       │  调用Tool从Milvus检索文本
└────────┬─────────┘
         ↓
┌──────────────────┐
│ analyze_core     │  核心指标分析节点
│  _indicators     │  LLM分析收入、利润
└────────┬─────────┘
         ↓
┌──────────────────┐
│ analyze_auxiliary│  辅助指标分析节点
│  _indicators     │  LLM分析毛利率、费用率
└────────┬─────────┘
         ↓
┌──────────────────┐
│ analyze_specific │  个性化指标分析节点
│  _indicators     │  LLM分析先导信号
└────────┬─────────┘
         ↓
┌──────────────────┐
│  generate_report │  报告生成节点
│                  │  LLM综合生成报告
└────────┬─────────┘
         ↓
┌──────────────────┐
│ quality_check    │  质量检查节点
│                  │  评分、决定是否重新生成
└────────┬─────────┘
         ↓
     [END/regenerate]
```

---

## 🔧 核心组件说明

### 1. Tools 层

#### 1.1 财务数据工具 (`src/tools/financial_data_tools.py`)

```python
@tool
def get_complete_financial_data_tool(
    stock_code: str,
    report_period: str,
    report_type: str = "A",
    include_previous: bool = True
) -> Dict[str, Any]:
    """获取完整财务数据（三张表 + 上期数据）"""
    # 调用 FinancialDataService
    # 返回结构化数据
```

**定义的工具**：
- `get_income_statement_tool` - 获取利润表
- `get_balance_sheet_tool` - 获取资产负债表
- `get_cash_flow_tool` - 获取现金流量表
- `get_complete_financial_data_tool` - 获取完整数据

#### 1.2 指标计算工具 (`src/tools/indicator_calculation_tools.py`)

```python
@tool
def calculate_revenue_growth_tool(
    current_revenue: float,
    previous_revenue: Optional[float] = None
) -> Dict[str, Any]:
    """计算营业收入增速"""
    # 代码精确计算
    # 避免LLM计算错误
```

**定义的工具**：
- `calculate_revenue_growth_tool` - 计算收入增速
- `calculate_profit_growth_tool` - 计算利润增速
- `calculate_gross_margin_tool` - 计算毛利率
- `calculate_rd_expense_ratio_tool` - 计算研发费用率
- `calculate_sales_expense_ratio_tool` - 计算销售费用率
- `calculate_all_indicators_tool` - 计算所有指标（使用IndicatorExtractor）

#### 1.3 Milvus 检索工具 (`src/tools/milvus_tools.py`)

```python
@tool
def get_context_for_analysis_tool(
    company_name: str,
    report_period: str,
    query: Optional[str] = None
) -> str:
    """获取用于分析的上下文文本"""
    # 调用 VectorRetriever
    # 返回组装好的上下文
```

**定义的工具**：
- `retrieve_by_period_tool` - 按期间检索
- `get_context_for_analysis_tool` - 获取分析上下文
- `retrieve_similar_content_tool` - 语义检索

### 2. Nodes 层

#### 2.1 数据节点 (`src/nodes/data_nodes.py`)

- `fetch_financial_data_node` - 获取财务数据
- `retrieve_context_node` - 检索Milvus上下文

#### 2.2 计算节点 (`src/nodes/calculation_nodes.py`)

- `calculate_indicators_node` - 计算所有指标

#### 2.3 分析节点 (`src/nodes/analysis_nodes.py`)

- `analyze_core_indicators_node` - 分析核心指标
- `analyze_auxiliary_indicators_node` - 分析辅助指标
- `analyze_specific_indicators_node` - 分析个性化指标

#### 2.4 报告节点 (`src/nodes/report_nodes.py`)

- `generate_report_node` - 生成最终报告
- `quality_check_node` - 质量检查

### 3. Graphs 层 (`src/graphs/financial_report_graph.py`)

**职责**：仅负责编排，不包含业务逻辑

```python
def create_graph() -> StateGraph:
    """创建工作流图"""
    workflow = StateGraph(FinancialReportState)
    
    # 添加节点
    workflow.add_node("fetch_financial_data", fetch_financial_data_node)
    workflow.add_node("calculate_indicators", calculate_indicators_node)
    # ...
    
    # 定义工作流路径
    workflow.add_edge("fetch_financial_data", "calculate_indicators")
    # ...
    
    return workflow.compile()
```

### 4. 状态管理 (`src/graphs/state.py`)

```python
class FinancialReportState(TypedDict, total=False):
    """财报分析状态"""
    # 输入信息
    company_name: str
    company_code: str
    report_period: str
    industry: str
    
    # 财务数据
    income_statement: Optional[Dict[str, Any]]
    balance_sheet: Optional[Dict[str, Any]]
    cash_flow: Optional[Dict[str, Any]]
    
    # 指标数据
    core_indicators: Dict[str, Any]
    auxiliary_indicators: Dict[str, Any]
    specific_indicators: Dict[str, Any]
    
    # 分析结果
    core_analysis: str
    auxiliary_analysis: str
    specific_analysis: str
    
    # 最终报告
    final_report: str
    
    # 元数据
    errors: List[str]
    tools_called: List[str]
    llm_calls: int
    processing_time: float
```

---

## 💡 设计优势

### 1. 职责单一

- **Tools**：只负责执行具体任务
- **Nodes**：只负责业务逻辑处理
- **Graphs**：只负责工作流编排

### 2. 易于扩展

**添加新指标**：
1. 在 `indicator_calculation_tools.py` 中定义新的Tool
2. 在 `calculate_indicators_node` 中调用新Tool
3. 无需修改工作流编排

**添加新节点**：
1. 在 `src/nodes/` 中创建新节点
2. 在 `financial_report_graph.py` 中添加节点
3. 定义节点连接关系

**添加新数据源**：
1. 在 `src/tools/` 中定义新的数据获取Tool
2. 在相关节点中调用新Tool
3. 无需修改其他模块

### 3. 可测试性

- 每个Tool可独立测试
- 每个Node可独立测试
- 工作流可整体测试

### 4. 可观察性

- 状态包含详细的处理步骤记录
- 记录所有调用的Tools
- 记录LLM调用次数
- 记录处理时间

---

## 🚀 使用示例

```python
from src.analysis.report_generator import ReportGenerator

# 创建报告生成器（内部使用LangGraph）
generator = ReportGenerator()

# 生成报告
result = generator.generate_report(
    company_name="三六零",
    company_code="601360",
    report_period="2024-03-31",
    industry="computer"
)

# 查看结果
print(f"成功: {result['success']}")
print(f"LLM调用: {result['llm_calls']}次")
print(f"处理时间: {result['processing_time']:.2f}秒")
print(f"质量评分: {result['quality_score']}")
print(f"\n报告:\n{result['report']}")
```

---

## 📝 注意事项

1. **环境配置**
   - 确保所有环境变量已配置（.env）
   - LangGraph 需要 `langgraph>=0.2.0`

2. **Tools 调用**
   - Tools 通过 `.invoke()` 方法调用
   - 参数必须是字典格式

3. **状态管理**
   - 状态在节点间自动传递
   - 节点函数必须返回更新后的状态

4. **错误处理**
   - 每个节点都有 try-except
   - 错误记录在 state["errors"] 中
   - 工作流可继续执行或优雅退出

---

## 📚 相关文档

- **需求文档**: `docs/需求文档.md`
- **系统架构**: `docs/系统架构设计.md`
- **API文档**: 各模块的 docstring

---

*本架构基于 LangChain + LangGraph 最佳实践设计*

