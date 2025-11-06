"""Milvus 检索 Tools

将 VectorRetriever 的功能封装为 LangChain Tools
"""
from typing import List, Dict, Optional
from langchain_core.tools import tool
from loguru import logger

from src.retrieval.vector_retriever import VectorRetriever


# 全局检索器实例
_retriever = None

def get_retriever() -> VectorRetriever:
    """获取向量检索器单例"""
    global _retriever
    if _retriever is None:
        _retriever = VectorRetriever()
    return _retriever


@tool
def retrieve_by_period_tool(
    company_name: str,
    report_period: str
) -> List[Dict]:
    """检索指定公司和期间的财报文本
    
    Args:
        company_name: 公司名称，如 "三六零"
        report_period: 报告期，如 "2024-03-31"
        
    Returns:
        检索结果列表，每条包含：
        - score: 相似度分数
        - report_id: 报告ID
        - company_name: 公司名称
        - report_period: 报告期
        - chunk_type: 文本块类型
        - text: 文本内容
    """
    logger.info(f"Tool调用: 检索财报 - {company_name} {report_period}")
    retriever = get_retriever()
    results = retriever.retrieve_by_period(company_name, report_period)
    logger.info(f"检索到 {len(results)} 条结果")
    return results


@tool
def get_context_for_analysis_tool(
    company_name: str,
    report_period: str,
    query: Optional[str] = None
) -> str:
    """获取用于分析的上下文文本
    
    整合当前期财报、历史财报对比和相关参考信息
    
    Args:
        company_name: 公司名称
        report_period: 报告期
        query: 可选的查询文本，用于检索相关内容
        
    Returns:
        组装好的上下文文本
    """
    logger.info(f"Tool调用: 获取分析上下文 - {company_name} {report_period}")
    retriever = get_retriever()
    context = retriever.get_context_for_analysis(company_name, report_period, query)
    logger.info(f"上下文长度: {len(context)} 字符")
    return context


@tool
def retrieve_similar_content_tool(
    query: str,
    top_k: int = 5
) -> List[Dict]:
    """语义检索相似内容
    
    Args:
        query: 查询文本
        top_k: 返回结果数量
        
    Returns:
        相似内容列表
    """
    logger.info(f"Tool调用: 语义检索 - {query[:50]}...")
    retriever = get_retriever()
    results = retriever.retrieve_similar_content(query, top_k)
    logger.info(f"检索到 {len(results)} 条相似内容")
    return results

