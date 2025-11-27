"""测试Milvus查询"""
from pymilvus import connections, Collection
from src.config.settings import settings
from sentence_transformers import SentenceTransformer
from src.embeddings.factory import EmbeddingFactory
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 全局 LLM 实例（避免重复初始化）
_llm = None

def get_llm() -> ChatOpenAI:
    """获取 LLM 单例"""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            model=settings.DEEPSEEK_MODEL,
            temperature=settings.DEEPSEEK_TEMPERATURE,
            max_tokens=settings.DEEPSEEK_MAX_TOKENS
        )
    return _llm

def test_query():
    """测试查询Milvus数据"""
    
    # 1. 连接Milvus
    print("连接Milvus...")
    connections.connect(
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT,
        user=settings.MILVUS_USER,
        password=settings.MILVUS_PASSWORD
    )
    print("✅ 已连接")
    
    # 2. 获取collection
    collection = Collection("financial_reports")
    collection.load()
    print(f"✅ Collection加载完成")
    
    # 3. 查看统计信息
    print(f"\n【统计信息】")
    print(f"总文档数: {collection.num_entities}")
    
    # 4. 查询所有数据（限制10条）
    print(f"\n【查询前10条数据】")
    results = collection.query(
        expr="chunk_index >= 0",
        output_fields=["report_id", "company_name", "chunk_type", "chunk_text"],
        limit=10
    )
    
    for i, result in enumerate(results, 1):
        print(f"\n--- 记录 {i} ---")
        print(f"报告ID: {result['report_id']}")
        print(f"公司: {result['company_name']}")
        print(f"类型: {result['chunk_type']}")
        print(f"文本预览: {result['chunk_text'][:100]}...")
    
    # 5. 向量搜索测试
    print(f"\n【向量搜索测试】")
    search_text = "公司主营业务"
    print(f"搜索关键词: {search_text}")
    
    # 加载embedding模型
    print("加载embedding模型...")
    model = SentenceTransformer(settings.EMBEDDING_MODEL, device='cpu')
    
    # 生成查询向量
    query_vector = model.encode([search_text])[0].tolist()
    print(f"查询向量维度: {len(query_vector)}")
    
    # 向量搜索
    search_results = collection.search(
        data=[query_vector],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"ef": 64}},
        limit=5,
        output_fields=["report_id", "company_name", "chunk_type", "title", "chunk_text"]
    )
    
    print(f"\n找到 {len(search_results[0])} 条相关结果:")
    for i, hit in enumerate(search_results[0], 1):
        print(f"\n--- TOP {i} (相似度: {hit.score:.4f}) ---")
        print(f"报告ID: {hit.entity.get('report_id')}")
        print(f"公司: {hit.entity.get('company_name')}")
        print(f"类型: {hit.entity.get('chunk_type')}")
        print(f"文本: {hit.entity.get('chunk_text')[:200]}...")
    
    print("\n✅ 测试完成！")


system_prompt = """
你是一位专业的财报分析师。你将收到用户的问题和与之相关的公司财报文档片段。请严格按照行业标准，结合这些文档内容，做出专业、客观的分析与总结，尤其关注财务健康、业务结构、主营业务、风险点和业务亮点。
输出时，请严格按照如下结构化格式返回：

【问题重述】
（简明重述用户问题）

【核心要点摘要】
（1-3句总结主要分析结论）

【详细分析】
（分点详细说明，引用相关文档内容佐证）

【结论与建议】
（结合行业背景、公司情况，要有针对性建议）

如遇信息不足，可明确指出所需补充数据类型，不可编造虚假内容。
"""

chunk_prompt = """
用户问题：{query}

相关文档摘要：
{chunks}
"""

def test_query_by_content(company_code: str, report_period: str, query: str):
    # 1. 连接Milvus
    print("连接Milvus...")
    connections.connect(
        host=settings.MILVUS_HOST,
        port=settings.MILVUS_PORT,
        user=settings.MILVUS_USER,
        password=settings.MILVUS_PASSWORD
    )
    print("✅ 已连接")
    
    # 2. 获取collection
    collection = Collection("financial_reports")
    collection.load()

    embedding_service = EmbeddingFactory.create_embedding_service()

    query_vector = embedding_service.encode([query])[0]
    search_results = collection.search(
        expr=f"company_code == '{company_code}' and report_period == '{report_period}'",
        data=[query_vector],
        anns_field="embedding",
        param={"metric_type": "COSINE", "params": {"ef": 64}},
        limit=10,
        output_fields=["chunk_text", "title", "chunk_type"]
    )

    chunk_texts = []
    for result in search_results[0]:
        chunk_texts.append(result.entity.get('chunk_text'))
    
    # 使用LLM对结果进行总结
    prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", chunk_prompt)
        ])
        
    llm = get_llm()
    chain = prompt | llm
    
    response = chain.invoke({
        "query": query,
        "chunks": chunk_texts
    })
    
    print(response.content)

if __name__ == "__main__":

    company_code = "601360"
    report_period = "20250630"

    print("=" * 40)
    print(f"{company_code} {report_period}财报点评")
    print("=" * 40)

    print("=" * 40)
    print("维度 1：战略与未来 (Strategy Context)")
    print("=" * 40)
    test_query_by_content(company_code, report_period, "公司未来的发展战略、经营计划和新年度业务目标")
    test_query_by_content(company_code, report_period, "核心技术研发投入重点、研发人员变动及新产品布局")
    test_query_by_content(company_code, report_period, "重大资本支出计划、募集资金使用情况及未来投资方向")
    test_query_by_content(company_code, report_period, "管理层对行业竞争格局和市场趋势的展望")
    print("=" * 40)
    print("维度 2：经营与业绩 (Performance Context)")
    print("=" * 40)
    test_query_by_content(company_code, report_period, "营业收入变动原因、主营业务分地区分产品情况")
    test_query_by_content(company_code, report_period, "毛利率波动的主要原因、成本结构变动分析")
    test_query_by_content(company_code, report_period, "主要客户和供应商的集中度变化、大客户依赖情况")
    test_query_by_content(company_code, report_period, "销售费用和管理费用的变动原因分析")
    print("=" * 40)
    print("维度 3：风险与隐患 (Risk Context)")
    print("=" * 40)
    test_query_by_content(company_code, report_period, "应收账款坏账准备计提情况、账龄结构及回款风险")
    test_query_by_content(company_code, report_period, "存货跌价准备计提原因、库存积压情况分析")
    test_query_by_content(company_code, report_period, "商誉减值测试情况、被并购标的业绩承诺完成情况")
    test_query_by_content(company_code, report_period, "重大未决诉讼、仲裁事项及对外担保情况")
    test_query_by_content(company_code, report_period, "公司面临的主要风险因素及应对措施")
    print("=" * 40)
    print("维度 4：现金流与质量 (Cash Flow Context)")
    print("=" * 40)
    test_query_by_content(company_code, report_period, "经营活动产生的现金流量净额与净利润差异的原因")
    test_query_by_content(company_code, report_period, "重大投资活动和筹资活动的现金流变动说明")

