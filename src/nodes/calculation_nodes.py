"""指标计算节点

负责调用 Tools 计算技术指标（代码计算，避免GIGO）
"""
from loguru import logger

from src.graphs.state import FinancialReportState
from src.tools import calculate_all_indicators_tool


def calculate_indicators_node(state: FinancialReportState) -> FinancialReportState:
    """节点: 计算指标
    
    调用 Tools 计算所有技术指标（代码计算，避免GIGO）
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("🔢 节点执行: 计算技术指标")
    state["current_step"] = "calculate_indicators"
    state["processing_steps"].append("calculate_indicators")
    
    if state["errors"]:
        logger.warning("⚠️ 前序节点有错误，跳过指标计算")
        return state
    
    try:
        # 调用Tool计算所有指标
        current_data = {
            "income_statement": state["income_statement"],
            "balance_sheet": state["balance_sheet"],
            "cash_flow": state["cash_flow"]
        }
        
        indicators = calculate_all_indicators_tool.invoke({
            "industry": state["industry"],
            "current_data": current_data,
            "previous_data": state.get("previous_data")
        })
        
        state["tools_called"].append("calculate_all_indicators_tool")
        
        # 更新状态
        state["all_indicators"] = indicators
        state["core_indicators"] = indicators.get("core", {})
        state["auxiliary_indicators"] = indicators.get("auxiliary", {})
        state["specific_indicators"] = indicators.get("specific", {})
        
        logger.success(f"✅ 计算完成: 核心{len(state['core_indicators'])}个, "
                     f"辅助{len(state['auxiliary_indicators'])}个, "
                     f"个性化{len(state['specific_indicators'])}个")
        
    except Exception as e:
        error_msg = f"计算指标失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        state["errors"].append(error_msg)
    
    return state

