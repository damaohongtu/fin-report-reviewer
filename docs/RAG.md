# 财报点评系统 RAG 策略设计文档

## 1. 背景与问题

当前系统已经将财报原始文档（PDF/Markdown）经过分块（Chunking）和向量化（Embedding）后存储在 Milvus 向量数据库中。在实际运行中，面临以下两个核心问题：

1.  **检索策略不明**：当前仅使用“公司名+报告期”进行模糊检索，缺乏针对性，难以精准获取支持“张新民财报分析方法论”所需的深度信息（如战略规划、隐形风险等）。
2.  **LLM 响应缓慢**：如果在检索阶段对每个问题都调用 LLM 进行总结（Summarization），会导致极高的延迟（Latency），且上下文窗口（Context Window）容易被无关信息填满。

本文档旨在基于张新民四维分析框架，设计一套高效的检索增强生成（RAG）策略。

---

## 2. 核心策略：基于张氏框架的分面检索 (Faceted Retrieval)

为了解决上述问题，我们放弃“泛泛检索+逐个总结”的模式，转而采用**“分面检索+按需组装”**的策略。

### 2.1 什么是分面检索？

不使用单一的 Query 去检索所有内容，而是根据分析维度（Dimensions），预定义一组**结构化查询（Structured Queries）**。

### 2.2 针对财报的四维检索清单

基于《张新民教你读财报》的四维框架，我们需要从向量库中精准“捞”出以下四类切片：

#### 🟢 维度 1：战略与未来 (Strategy Context)
*目标：获取MD&A中关于未来的描述，用于战略分析节点。*

**检索 Queries**:
1.  "公司未来的发展战略、经营计划和新年度业务目标"
2.  "核心技术研发投入重点、研发人员变动及新产品布局"
3.  "重大资本支出计划、募集资金使用情况及未来投资方向"
4.  "管理层对行业竞争格局和市场趋势的展望"

#### 🔵 维度 2：经营与业绩 (Performance Context)
*目标：解释收入、利润、毛利的变动原因，用于竞争力分析节点。*

**检索 Queries**:
1.  "营业收入变动原因、主营业务分地区分产品情况"
2.  "毛利率波动的主要原因、成本结构变动分析"
3.  "主要客户和供应商的集中度变化、大客户依赖情况"
4.  "销售费用和管理费用的变动原因分析"

#### 🔴 维度 3：风险与隐患 (Risk Context)
*目标：挖掘报表附注中的风险点，用于风险分析节点。*

**检索 Queries**:
1.  "应收账款坏账准备计提情况、账龄结构及回款风险"
2.  "存货跌价准备计提原因、库存积压情况分析"
3.  "商誉减值测试情况、被并购标的业绩承诺完成情况"
4.  "重大未决诉讼、仲裁事项及对外担保情况"
5.  "公司面临的主要风险因素及应对措施"

#### 🟡 维度 4：现金流与质量 (Cash Flow Context)
*目标：辅助判断利润含金量。*

**检索 Queries**:
1.  "经营活动产生的现金流量净额与净利润差异的原因"
2.  "重大投资活动和筹资活动的现金流变动说明"

---

## 3. 工作流设计与数据流转

我们将 RAG 过程拆解为**检索（Retrieve）**和**生成（Generate）**两个解耦的阶段。

### 3.1 改造 `retrieve_context_node`

在此节点中，**不调用 LLM**，只进行纯向量检索。

```python
# 伪代码逻辑
def retrieve_context_node(state):
    # 1. 并行执行四组检索
    strategy_chunks = milvus.search(queries=STRATEGY_QUERIES, top_k=5)
    performance_chunks = milvus.search(queries=PERFORMANCE_QUERIES, top_k=5)
    risk_chunks = milvus.search(queries=RISK_QUERIES, top_k=5)
    
    # 2. 去重与清洗 (Deduplication)
    # 因为不同Query可能召回相同的Chunk，需要按Chunk ID去重
    state["strategy_context"] = deduplicate(strategy_chunks)
    state["performance_context"] = deduplicate(performance_chunks)
    state["risk_context"] = deduplicate(risk_chunks)
    
    return state
```

### 3.2 改造分析节点 (Analysis Nodes)

各分析节点只消费自己相关的 Context，避免一次性把 10k token 塞给 LLM。

*   **`analyze_strategy_node`**: 输入 `state["strategy_context"]` + 研发费用数据。
*   **`analyze_core_indicators_node`**: 输入 `state["performance_context"]` + 收入/利润数据。
*   **`analyze_risk_node`**: 输入 `state["risk_context"]` + 应收/存货数据。

### 3.3 性能优化收益

1.  **降低 Latency**：
    *   检索阶段无 LLM 调用，毫秒级完成。
    *   分析阶段各节点并行执行（LangGraph 支持），且每个节点的 Context 变短了，生成速度提升。
2.  **提升准确率 (Accuracy)**：
    *   “风险分析”节点不会被“战略规划”的宏大叙事干扰。
    *   “战略分析”节点不会被“坏账计提”的细节淹没。
    *   LLM 的注意力机制（Attention）能更聚焦。

---

## 4. 进阶优化建议

### 4.1 Hybrid Search (混合检索)
对于专有名词（如“应收账款”、“商誉”），关键词检索（BM25）往往比向量检索更精准。建议在 Milvus 检索时结合关键词匹配，或者先用关键词过滤再做向量相似度计算。

### 4.2 Re-ranking (重排序)
如果检索回来的 Chunks 较多（例如每个维度召回 20 个），直接拼接会超长。
建议引入一个轻量级的 **Cross-Encoder Re-ranker**（如 BGE-Reranker），对召回结果进行二次打分，只取最相关的 Top-5 给 LLM。
*注：Re-ranker 比 LLM 快得多，性价比极高。*

### 4.3 Metadata Filtering (元数据过滤)
在 Chunking 阶段，我们已经保留了标题层级（Heading Hierarchy）。
检索时可以利用 Filter：
*   查战略时，优先看 `section_title` 包含 "管理层讨论"、"未来展望" 的 Chunk。
*   查风险时，优先看 `section_title` 包含 "风险"、"重要事项" 的 Chunk。

## 5. 总结

| 优化项 | 旧模式 | 新模式 (张氏 RAG) |
| :--- | :--- | :--- |
| **检索 Query** | "公司名 + 2024Q1" | 细分为战略/经营/风险等 15+ 个具体问题 |
| **检索结果** | 杂乱的大杂烩 | 按维度分类的结构化 Context |
| **LLM 调用** | 检索后立即总结 (串行, 慢) | 推迟到分析节点 (并行, 快) |
| **Context 长度** | 容易超长，噪音大 | 短小精悍，信噪比高 |

通过这种**分而治之**的策略，我们既解决了“检索什么”的业务问题，也解决了“调用慢”的技术问题。

