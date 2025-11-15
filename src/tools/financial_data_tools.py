"""财务数据获取 Tools

将财报数据HTTP客户端的功能封装为 LangChain Tools
"""
from typing import Dict, Any
from langchain_core.tools import tool
from loguru import logger

from src.clients.financial_data_http_client import FinancialDataHttpClient


# 全局HTTP客户端实例
_http_client = None

def get_data_client() -> FinancialDataHttpClient:
    """获取财报数据HTTP客户端单例"""
    global _http_client
    if _http_client is None:
        _http_client = FinancialDataHttpClient()
    return _http_client


@tool
def get_income_statement_tool(
    stock_code: str,
    report_period: str,
    report_type: str = "A"
) -> Dict[str, Any]:
    """获取利润表数据
    
    Args:
        stock_code: 股票代码，如 "601360"
        report_period: 报告期，如 "2024-03-31"
        report_type: 报表类型，A=合并报表，B=母公司报表
        
    Returns:
        利润表数据字典，包含营业收入、成本、费用、利润等
    """
    logger.info(f"Tool调用: 获取利润表 - {stock_code} {report_period}")
    client = get_data_client()
    result = client.get_income_statement(stock_code, report_period, report_type)
    return result or {}


@tool
def get_balance_sheet_tool(
    stock_code: str,
    report_period: str,
    report_type: str = "A"
) -> Dict[str, Any]:
    """获取资产负债表数据
    
    Args:
        stock_code: 股票代码
        report_period: 报告期
        report_type: 报表类型
        
    Returns:
        资产负债表数据字典，包含资产、负债、权益等
    """
    logger.info(f"Tool调用: 获取资产负债表 - {stock_code} {report_period}")
    client = get_data_client()
    result = client.get_balance_sheet(stock_code, report_period, report_type)
    return result or {}


@tool
def get_cash_flow_tool(
    stock_code: str,
    report_period: str,
    report_type: str = "A"
) -> Dict[str, Any]:
    """获取现金流量表数据
    
    Args:
        stock_code: 股票代码
        report_period: 报告期
        report_type: 报表类型
        
    Returns:
        现金流量表数据字典，包含经营、投资、筹资活动现金流
    """
    logger.info(f"Tool调用: 获取现金流量表 - {stock_code} {report_period}")
    client = get_data_client()
    result = client.get_cash_flow(stock_code, report_period, report_type)
    return result or {}


@tool
def get_complete_financial_data_tool(
    stock_code: str,
    report_period: str,
    report_type: str = "A",
    include_previous: bool = True
) -> Dict[str, Any]:
    """获取完整财务数据（三张表 + 上期数据）
    
    Args:
        stock_code: 股票代码
        report_period: 报告期
        report_type: 报表类型
        include_previous: 是否包含上期数据
        
    Returns:
        完整财务数据，包含：
        - income_statement: 利润表
        - balance_sheet: 资产负债表
        - cash_flow: 现金流量表
        - previous_period: 上期期间
        - previous_data: 上期数据
    """
    logger.info(f"Tool调用: 获取完整财务数据 - {stock_code} {report_period}")
    client = get_data_client()
    result = client.get_complete_financial_data(
        stock_code, report_period, report_type, include_previous
    )
    return result

