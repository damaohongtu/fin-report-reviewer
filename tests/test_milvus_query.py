"""测试Milvus查询"""
from pymilvus import connections, Collection
from src.config.settings import settings
from sentence_transformers import SentenceTransformer

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
        output_fields=["report_id", "company_name", "chunk_type", "chunk_text"]
    )
    
    print(f"\n找到 {len(search_results[0])} 条相关结果:")
    for i, hit in enumerate(search_results[0], 1):
        print(f"\n--- TOP {i} (相似度: {hit.score:.4f}) ---")
        print(f"报告ID: {hit.entity.get('report_id')}")
        print(f"公司: {hit.entity.get('company_name')}")
        print(f"类型: {hit.entity.get('chunk_type')}")
        print(f"文本: {hit.entity.get('chunk_text')[:200]}...")
    
    print("\n✅ 测试完成！")

if __name__ == "__main__":
    test_query()

