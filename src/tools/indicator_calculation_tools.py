"""指标计算 Tools

将各种财务指标计算封装为独立的 LangChain Tools
每个 Tool 负责一个具体的指标计算，避免 LLM 计算导致的 GIGO
"""
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from loguru import logger

from src.extractors.indicator_extractor import IndicatorExtractor


@tool
def calculate_revenue_growth_tool(
    current_revenue: float,
    previous_revenue: Optional[float] = None
) -> Dict[str, Any]:
    """计算营业收入增速
    
    Args:
        current_revenue: 本期营业收入
        previous_revenue: 上期营业收入（可选）
        
    Returns:
        收入增速数据，包含增长率、显示格式等
    """
    logger.info(f"Tool调用: 计算营业收入增速 - 本期:{current_revenue}, 上期:{previous_revenue}")
    
    growth_rate = None
    if previous_revenue and previous_revenue != 0:
        growth_rate = ((current_revenue - previous_revenue) / abs(previous_revenue)) * 100
        growth_rate = round(growth_rate, 2)
    
    result = {
        "name": "营业收入增速",
        "current": current_revenue,
        "previous": previous_revenue,
        "growth_rate": growth_rate,
        "display_format": _format_large_number(current_revenue)
    }
    
    logger.info(f"计算结果: 增长率={growth_rate}%")
    return result


@tool
def calculate_profit_growth_tool(
    current_profit: float,
    previous_profit: Optional[float] = None
) -> Dict[str, Any]:
    """计算净利润增速
    
    Args:
        current_profit: 本期净利润
        previous_profit: 上期净利润（可选）
        
    Returns:
        利润增速数据，包含增长率、显示格式等
    """
    logger.info(f"Tool调用: 计算净利润增速 - 本期:{current_profit}, 上期:{previous_profit}")
    
    growth_rate = None
    if previous_profit and previous_profit != 0:
        growth_rate = ((current_profit - previous_profit) / abs(previous_profit)) * 100
        growth_rate = round(growth_rate, 2)
    
    result = {
        "name": "净利润增速",
        "current": current_profit,
        "previous": previous_profit,
        "growth_rate": growth_rate,
        "display_format": _format_large_number(current_profit)
    }
    
    logger.info(f"计算结果: 增长率={growth_rate}%")
    return result


@tool
def calculate_gross_margin_tool(
    revenue: float,
    cost: float
) -> Dict[str, Any]:
    """计算毛利率
    
    Args:
        revenue: 营业收入
        cost: 营业成本
        
    Returns:
        毛利率数据
    """
    logger.info(f"Tool调用: 计算毛利率 - 收入:{revenue}, 成本:{cost}")
    
    gross_margin = None
    if revenue and cost and revenue != 0:
        gross_profit = revenue - cost
        gross_margin = (gross_profit / revenue) * 100
        gross_margin = round(gross_margin, 2)
    
    result = {
        "name": "毛利率",
        "value": gross_margin,
        "unit": "%"
    }
    
    logger.info(f"计算结果: 毛利率={gross_margin}%")
    return result


@tool
def calculate_rd_expense_ratio_tool(
    rd_expense: float,
    revenue: float
) -> Dict[str, Any]:
    """计算研发费用率
    
    Args:
        rd_expense: 研发费用
        revenue: 营业收入
        
    Returns:
        研发费用率数据
    """
    logger.info(f"Tool调用: 计算研发费用率 - 研发:{rd_expense}, 收入:{revenue}")
    
    rd_ratio = None
    if rd_expense and revenue and revenue != 0:
        rd_ratio = (rd_expense / revenue) * 100
        rd_ratio = round(rd_ratio, 2)
    
    result = {
        "name": "研发费用率",
        "expense": rd_expense,
        "ratio": rd_ratio,
        "display_format": _format_large_number(rd_expense),
        "unit": "%"
    }
    
    logger.info(f"计算结果: 研发费用率={rd_ratio}%")
    return result


@tool
def calculate_sales_expense_ratio_tool(
    sales_expense: float,
    revenue: float
) -> Dict[str, Any]:
    """计算销售费用率
    
    Args:
        sales_expense: 销售费用
        revenue: 营业收入
        
    Returns:
        销售费用率数据
    """
    logger.info(f"Tool调用: 计算销售费用率 - 销售费用:{sales_expense}, 收入:{revenue}")
    
    sales_ratio = None
    if sales_expense and revenue and revenue != 0:
        sales_ratio = (sales_expense / revenue) * 100
        sales_ratio = round(sales_ratio, 2)
    
    result = {
        "name": "销售费用率",
        "expense": sales_expense,
        "ratio": sales_ratio,
        "display_format": _format_large_number(sales_expense),
        "unit": "%"
    }
    
    logger.info(f"计算结果: 销售费用率={sales_ratio}%")
    return result


@tool
def calculate_all_indicators_tool(
    industry: str,
    current_data: Dict[str, Any],
    previous_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """计算所有指标（使用 IndicatorExtractor）
    
    Args:
        industry: 行业代码
        current_data: 当期财务数据
        previous_data: 上期财务数据（可选）
        
    Returns:
        按优先级分类的所有指标
    """
    logger.info(f"Tool调用: 计算所有指标 - 行业:{industry}")
    
    extractor = IndicatorExtractor(industry)
    indicators = extractor.extract_indicators(current_data, previous_data)
    
    logger.info(f"计算完成: 核心{len(indicators['core'])}个, 辅助{len(indicators['auxiliary'])}个, 个性化{len(indicators['specific'])}个")
    return indicators


def _format_large_number(number: float) -> str:
    """格式化大数字显示"""
    if number is None:
        return "N/A"
    
    abs_number = abs(number)
    sign = "-" if number < 0 else ""
    
    if abs_number >= 100_000_000:  # 亿
        return f"{sign}{abs_number / 100_000_000:.2f}亿"
    elif abs_number >= 10_000:  # 万
        return f"{sign}{abs_number / 10_000:.2f}万"
    else:
        return f"{sign}{abs_number:.2f}"

