"""LangGraph 状态定义

定义财报分析工作流的状态结构
"""
from typing import Dict, List, Any, Optional, TypedDict
from datetime import datetime


class FinancialReportState(TypedDict, total=False):
    """财报分析状态
    
    用于在 LangGraph 节点之间传递数据
    """
    # ===== 输入信息 =====
    company_name: str  # 公司名称
    company_code: str  # 股票代码
    report_period: str  # 报告期
    industry: str  # 行业
    report_type: str  # 报表类型(A=合并,B=母公司)
    
    # ===== 财务数据 =====
    income_statement: Optional[Dict[str, Any]]  # 利润表
    balance_sheet: Optional[Dict[str, Any]]  # 资产负债表
    cash_flow: Optional[Dict[str, Any]]  # 现金流量表
    previous_period: Optional[str]  # 上期期间
    previous_data: Optional[Dict[str, Any]]  # 上期数据
    
    # ===== 指标数据 =====
    core_indicators: Dict[str, Any]  # 核心指标
    auxiliary_indicators: Dict[str, Any]  # 辅助指标
    specific_indicators: Dict[str, Any]  # 个性化指标
    all_indicators: Dict[str, Any]  # 所有指标汇总
    
    # ===== 非结构化数据 =====
    milvus_context: str  # Milvus检索的上下文
    retrieved_chunks: List[Dict]  # 检索到的文本块
    
    # ===== 分析结果 =====
    core_analysis: str  # 核心指标分析
    auxiliary_analysis: str  # 辅助指标分析
    specific_analysis: str  # 个性化指标分析
    comprehensive_judgment: str  # 综合判断
    investment_advice: str  # 投资建议
    
    # ===== 最终报告 =====
    final_report: str  # 最终生成的报告
    report_quality_score: float  # 报告质量评分
    
    # ===== 元数据 =====
    errors: List[str]  # 错误列表
    warnings: List[str]  # 警告列表
    processing_steps: List[str]  # 处理步骤记录
    llm_calls: int  # LLM调用次数
    tools_called: List[str]  # 已调用的Tools列表
    created_at: datetime  # 创建时间
    processing_time: float  # 处理耗时(秒)
    
    # ===== 流程控制 =====
    current_step: str  # 当前步骤
    should_regenerate: bool  # 是否需要重新生成
    regeneration_count: int  # 重新生成次数


def create_initial_state(
    company_name: str,
    company_code: str,
    report_period: str,
    industry: str,
    report_type: str = "A"
) -> FinancialReportState:
    """创建初始状态
    
    Args:
        company_name: 公司名称
        company_code: 股票代码
        report_period: 报告期
        industry: 行业
        report_type: 报表类型
        
    Returns:
        初始化的状态字典
    """
    return FinancialReportState(
        # 输入信息
        company_name=company_name,
        company_code=company_code,
        report_period=report_period,
        industry=industry,
        report_type=report_type,
        
        # 数据初始化
        income_statement=None,
        balance_sheet=None,
        cash_flow=None,
        previous_period=None,
        previous_data=None,
        
        # 指标初始化
        core_indicators={},
        auxiliary_indicators={},
        specific_indicators={},
        all_indicators={},
        
        # 非结构化数据初始化
        milvus_context="",
        retrieved_chunks=[],
        
        # 分析结果初始化
        core_analysis="",
        auxiliary_analysis="",
        specific_analysis="",
        comprehensive_judgment="",
        investment_advice="",
        
        # 报告初始化
        final_report="",
        report_quality_score=0.0,
        
        # 元数据初始化
        errors=[],
        warnings=[],
        processing_steps=[],
        llm_calls=0,
        tools_called=[],
        created_at=datetime.now(),
        processing_time=0.0,
        
        # 流程控制初始化
        current_step="init",
        should_regenerate=False,
        regeneration_count=0
    )

