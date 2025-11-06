"""财报分析 LangGraph 工作流

使用 LangGraph 编排整个财报分析流程
只负责定义工作流结构，节点实现在 nodes 模块中
"""
from typing import Literal
from loguru import logger

from langgraph.graph import StateGraph, END

from src.graphs.state import FinancialReportState
from src.nodes import (
    fetch_financial_data_node,
    calculate_indicators_node,
    retrieve_context_node,
    analyze_core_indicators_node,
    analyze_auxiliary_indicators_node,
    analyze_specific_indicators_node,
    generate_report_node,
    quality_check_node
)


def create_graph() -> StateGraph:
    """创建工作流图
    
    只负责编排，定义节点连接关系
    
    Returns:
        编译后的工作流图
    """
    logger.info("🔧 创建 LangGraph 工作流")
    
    # 创建状态图
    workflow = StateGraph(FinancialReportState)
    
    # 添加节点（引用独立的节点函数）
    workflow.add_node("fetch_financial_data", fetch_financial_data_node)
    workflow.add_node("calculate_indicators", calculate_indicators_node)
    workflow.add_node("retrieve_context", retrieve_context_node)
    workflow.add_node("analyze_core_indicators", analyze_core_indicators_node)
    workflow.add_node("analyze_auxiliary_indicators", analyze_auxiliary_indicators_node)
    workflow.add_node("analyze_specific_indicators", analyze_specific_indicators_node)
    workflow.add_node("generate_report", generate_report_node)
    workflow.add_node("quality_check", quality_check_node)
    
    # 设置入口点
    workflow.set_entry_point("fetch_financial_data")
    
    # 定义工作流路径（DAG）
    workflow.add_edge("fetch_financial_data", "calculate_indicators")
    workflow.add_edge("calculate_indicators", "retrieve_context")
    workflow.add_edge("retrieve_context", "analyze_core_indicators")
    workflow.add_edge("analyze_core_indicators", "analyze_auxiliary_indicators")
    workflow.add_edge("analyze_auxiliary_indicators", "analyze_specific_indicators")
    workflow.add_edge("analyze_specific_indicators", "generate_report")
    workflow.add_edge("generate_report", "quality_check")
    
    # 质量检查后的条件路由
    workflow.add_conditional_edges(
        "quality_check",
        route_after_quality_check,
        {
            "end": END,
            "regenerate": "generate_report"
        }
    )
    
    # 编译工作流
    compiled = workflow.compile()
    logger.success("✅ LangGraph 工作流创建完成")
    
    return compiled


# ==================== 路由函数 ====================

def route_after_quality_check(
    state: FinancialReportState
) -> Literal["end", "regenerate"]:
    """质量检查后的路由
    
    根据质量评分决定是结束还是重新生成
    
    Args:
        state: 当前状态
        
    Returns:
        下一个节点的名称
    """
    if state.get("should_regenerate", False):
        return "regenerate"
    else:
        return "end"


def create_financial_report_graph() -> StateGraph:
    """创建财报分析工作流图
    
    工厂函数，创建并返回编译后的工作流
    
    Returns:
        编译后的工作流图
    """
    return create_graph()
