"""财报点评报告生成器

使用 LangGraph 编排整个财报分析流程
通过状态机管理工作流，Tools 执行具体任务
"""
from typing import Dict, Any
from datetime import datetime

from loguru import logger

from src.graphs import create_initial_state, create_financial_report_graph


class ReportGenerator:
    """财报点评报告生成器
    
    基于 LangGraph 编排的财报分析工作流
    """
    
    def __init__(self):
        """初始化生成器"""
        # 创建 LangGraph 工作流
        self.graph = create_financial_report_graph()
        
        logger.success("✅ 报告生成器初始化完成（基于LangGraph）")
    
    def generate_report(
        self,
        company_name: str,
        company_code: str,
        report_period: str,
        industry: str,
        report_type: str = "A"
    ) -> Dict[str, Any]:
        """生成财报点评报告
        
        使用 LangGraph 工作流处理整个分析流程
        
        Args:
            company_name: 公司名称
            company_code: 公司代码
            report_period: 报告期，如"2024-03-31"
            industry: 行业
            report_type: 报表类型，A=合并报表
            
        Returns:
            包含报告内容和元数据的字典
        """
        logger.info(f"开始生成财报点评报告: {company_name} {report_period}")
        
        start_time = datetime.now()
        
        try:
            # 创建初始状态
            initial_state = create_initial_state(
                company_name=company_name,
                company_code=company_code,
                report_period=report_period,
                industry=industry,
                report_type=report_type
            )
            
            # 执行 LangGraph 工作流
            logger.info("🚀 执行 LangGraph 工作流")
            final_state = self.graph.invoke(initial_state)
            
            # 计算处理时间
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # 构建返回结果
            result = {
                "success": len(final_state.get("errors", [])) == 0,
                "company_name": company_name,
                "company_code": company_code,
                "report_period": report_period,
                "industry": industry,
                "report": final_state.get("final_report", ""),
                "indicators": final_state.get("all_indicators", {}),
                "processing_time": processing_time,
                "generated_at": end_time.isoformat(),
                "llm_calls": final_state.get("llm_calls", 0),
                "tools_called": final_state.get("tools_called", []),
                "processing_steps": final_state.get("processing_steps", []),
                "quality_score": final_state.get("report_quality_score", 0.0),
                "errors": final_state.get("errors", []),
                "warnings": final_state.get("warnings", [])
            }
            
            if result["success"]:
                logger.success(f"✅ 报告生成完成，耗时: {processing_time:.2f}秒")
                logger.info(f"   LLM调用: {result['llm_calls']}次")
                logger.info(f"   质量评分: {result['quality_score']}")
            else:
                logger.error(f"❌ 报告生成失败: {result['errors']}")
            
            return result
            
        except Exception as e:
            logger.exception(f"❌ 报告生成异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "company_name": company_name,
                "company_code": company_code,
                "report_period": report_period,
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
