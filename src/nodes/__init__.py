"""节点模块

每个节点是独立的处理单元，由 LangGraph 调用
"""

from src.nodes.data_nodes import (
    fetch_financial_data_node,
    retrieve_context_node
)

from src.nodes.calculation_nodes import (
    calculate_indicators_node
)

from src.nodes.analysis_nodes import (
    analyze_core_indicators_node,
    analyze_auxiliary_indicators_node,
    analyze_specific_indicators_node
)

from src.nodes.report_nodes import (
    generate_report_node,
    quality_check_node
)

__all__ = [
    # 数据节点
    "fetch_financial_data_node",
    "retrieve_context_node",
    
    # 计算节点
    "calculate_indicators_node",
    
    # 分析节点
    "analyze_core_indicators_node",
    "analyze_auxiliary_indicators_node",
    "analyze_specific_indicators_node",
    
    # 报告节点
    "generate_report_node",
    "quality_check_node",
]

