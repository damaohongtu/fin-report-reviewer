"""报告生成节点

负责生成最终报告和质量检查
"""
import re
from datetime import datetime
from loguru import logger
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.graphs.state import FinancialReportState
from src.config.settings import settings
from src.config.prompts import prompt_manager


# 全局 LLM 实例（避免重复初始化）
_llm = None

def get_llm() -> ChatOpenAI:
    """获取 LLM 单例"""
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL,
            model=settings.DEEPSEEK_MODEL,
            temperature=settings.DEEPSEEK_TEMPERATURE,
            max_tokens=settings.DEEPSEEK_MAX_TOKENS
        )
    return _llm


def generate_report_node(state: FinancialReportState) -> FinancialReportState:
    """节点: 生成最终报告
    
    使用 LLM 综合所有分析结果生成报告
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("📝 节点执行: 生成最终报告")
    state["current_step"] = "generate_report"
    state["processing_steps"].append("generate_report")
    
    try:
        # 构建提示词
        system_prompt = prompt_manager.get_system_prompt(state["industry"])
        report_prompt = prompt_manager.get_report_generation_prompt()
        
        # 限制上下文长度
        max_context_length = 2000
        milvus_context = state["milvus_context"]
        if len(milvus_context) > max_context_length:
            milvus_context = milvus_context[:max_context_length] + "\n...(内容过长，已截断)"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", report_prompt)
        ])
        
        llm = get_llm()
        chain = prompt | llm
        
        response = chain.invoke({
            "company_name": state["company_name"],
            "report_period": state["report_period"],
            "industry": state["industry"],
            "core_analysis": state["core_analysis"],
            "auxiliary_analysis": state["auxiliary_analysis"],
            "specific_analysis": state["specific_analysis"],
            "unstructured_context": milvus_context
        })
        
        state["final_report"] = response.content
        state["llm_calls"] += 1
        
        logger.success("✅ 最终报告生成完成")
        
    except Exception as e:
        error_msg = f"生成报告失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        state["errors"].append(error_msg)
        state["final_report"] = "报告生成失败。"
    
    return state


def quality_check_node(state: FinancialReportState) -> FinancialReportState:
    """节点: 质量检查
    
    检查报告质量，决定是否需要重新生成
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("✔️ 节点执行: 质量检查")
    state["current_step"] = "quality_check"
    state["processing_steps"].append("quality_check")
    
    if not state["final_report"]:
        state["report_quality_score"] = 0.0
        state["should_regenerate"] = False
        return state
    
    # 简单的质量评分
    score = 100.0
    issues = []
    
    # 检查报告长度
    if len(state["final_report"]) < 500:
        issues.append("报告过短")
        score -= 20
    
    # 检查关键章节
    required_sections = ["核心结论", "分项分析", "综合判断", "投资建议"]
    for section in required_sections:
        if section not in state["final_report"]:
            issues.append(f"缺少{section}章节")
            score -= 15
    
    # 检查是否有数据
    numbers = re.findall(r'\d+\.?\d*%?', state["final_report"])
    if len(numbers) < 5:
        issues.append("报告中数据引用不足")
        score -= 10
    
    state["report_quality_score"] = max(0.0, score)
    
    # 决定是否重新生成
    max_regenerations = 2
    if score < 60 and state["regeneration_count"] < max_regenerations:
        state["should_regenerate"] = True
        state["regeneration_count"] += 1
        logger.warning(f"⚠️ 报告质量不达标(评分:{score})，准备第{state['regeneration_count']}次重新生成")
    else:
        state["should_regenerate"] = False
        if issues:
            logger.warning(f"⚠️ 报告质量评分:{score}，存在问题:{issues}")
        else:
            logger.success(f"✅ 报告质量检查通过，评分:{score}")
    
    # 计算处理时间
    if state.get("created_at"):
        processing_time = (datetime.now() - state["created_at"]).total_seconds()
        state["processing_time"] = processing_time
    
    return state

