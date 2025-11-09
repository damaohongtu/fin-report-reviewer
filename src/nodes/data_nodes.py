"""数据获取节点

负责从数据源（PostgreSQL、Milvus）获取数据
"""
from loguru import logger

from src.graphs.state import FinancialReportState
from src.tools import (
    get_complete_financial_data_tool,
    get_context_for_analysis_tool
)


def fetch_financial_data_node(state: FinancialReportState) -> FinancialReportState:
    """节点: 获取财务数据
    
    调用 Tools 从 PostgreSQL 获取财报三表数据
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("📊 节点执行: 获取财务数据")
    state["current_step"] = "fetch_financial_data"
    state["processing_steps"].append("fetch_financial_data")
    
    try:
        # 调用Tool获取完整财务数据
        financial_data = get_complete_financial_data_tool.invoke({
            "stock_code": state["company_code"],
            "report_period": state["report_period"],
            "report_type": state.get("report_type", "A"),
            "include_previous": True
        })
        
        state["tools_called"].append("get_complete_financial_data_tool")
        
        # 更新状态
        state["income_statement"] = financial_data.get("income_statement")
        state["balance_sheet"] = financial_data.get("balance_sheet")
        state["cash_flow"] = financial_data.get("cash_flow")
        state["previous_period"] = financial_data.get("previous_period")
        state["previous_data"] = financial_data.get("previous_data")
        
        if not state["income_statement"]:
            state["errors"].append(f"未找到{state['company_code']}的{state['report_period']}期财报数据")
        else:
            logger.success(f"✅ 成功获取财务数据")
            
    except Exception as e:
        error_msg = f"获取财务数据失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        state["errors"].append(error_msg)
    
    return state


def retrieve_context_node(state: FinancialReportState) -> FinancialReportState:
    """节点: 检索上下文
    
    调用 Tools 从 Milvus 检索非结构化财报文本
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("📄 节点执行: 检索Milvus上下文")
    state["current_step"] = "retrieve_context"
    state["processing_steps"].append("retrieve_context")
    
    try:
        # 调用Tool获取上下文
        context = get_context_for_analysis_tool.invoke({
            "company_name": state["company_name"],
            "report_period": state["report_period"],
            "query": None
        })
        
        state["tools_called"].append("get_context_for_analysis_tool")
        state["milvus_context"] = context
        
        logger.success(f"✅ 检索到上下文: {len(context)} 字符")
        
    except Exception as e:
        error_msg = f"检索上下文失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        state["warnings"].append(error_msg)
        state["milvus_context"] = ""
    
    return state

