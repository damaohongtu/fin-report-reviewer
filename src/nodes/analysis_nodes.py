"""分析节点

负责使用 LLM 分析指标和生成洞察
"""
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


def analyze_core_indicators_node(state: FinancialReportState) -> FinancialReportState:
    """节点: 分析核心指标
    
    使用 LLM 分析核心指标（收入、利润）
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("🤖 节点执行: LLM分析核心指标")
    state["current_step"] = "analyze_core_indicators"
    state["processing_steps"].append("analyze_core_indicators")
    
    if not state["core_indicators"]:
        logger.warning("⚠️ 无核心指标数据，跳过分析")
        state["core_analysis"] = "核心指标数据缺失，无法分析。"
        return state
    
    try:
        # 准备核心指标数据文本
        core_data_lines = []
        for key, value in state["core_indicators"].items():
            name = value.get("name", key)
            current = value.get("display_format", "N/A")
            growth = value.get("growth_rate")
            
            if growth is not None:
                core_data_lines.append(f"- {name}: {current}元，同比增长 {growth:+.2f}%")
            else:
                core_data_lines.append(f"- {name}: {current}元")
        
        core_data_text = "\n".join(core_data_lines)
        
        # 构建提示词
        system_prompt = prompt_manager.get_system_prompt(state["industry"])
        analysis_prompt = prompt_manager.get_core_analysis_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", analysis_prompt)
        ])
        
        llm = get_llm()
        chain = prompt | llm
        
        response = chain.invoke({
            "company_name": state["company_name"],
            "report_period": state["report_period"],
            "industry": state["industry"],
            "core_indicators_data": core_data_text
        })
        
        state["core_analysis"] = response.content
        state["llm_calls"] += 1
        
        logger.success("✅ 核心指标分析完成")
        
    except Exception as e:
        error_msg = f"核心指标分析失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        state["errors"].append(error_msg)
        state["core_analysis"] = "分析失败。"
    
    return state


def analyze_auxiliary_indicators_node(state: FinancialReportState) -> FinancialReportState:
    """节点: 分析辅助指标
    
    使用 LLM 分析辅助指标（毛利率、费用率）
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("🤖 节点执行: LLM分析辅助指标")
    state["current_step"] = "analyze_auxiliary_indicators"
    state["processing_steps"].append("analyze_auxiliary_indicators")
    
    if not state["auxiliary_indicators"]:
        logger.warning("⚠️ 无辅助指标数据，跳过分析")
        state["auxiliary_analysis"] = "辅助指标数据缺失，无法分析。"
        return state
    
    try:
        # 准备辅助指标数据文本
        aux_data_lines = []
        for key, value in state["auxiliary_indicators"].items():
            name = value.get("name", key)
            
            if "ratio" in value:
                ratio = value.get("ratio")
                ratio_change = value.get("ratio_change")
                if ratio_change is not None:
                    aux_data_lines.append(f"- {name}: {ratio:.2f}%，变动 {ratio_change:+.2f}pp")
                else:
                    aux_data_lines.append(f"- {name}: {ratio:.2f}%")
            else:
                current = value.get("display_format", "N/A")
                growth = value.get("growth_rate")
                if growth is not None:
                    aux_data_lines.append(f"- {name}: {current}元，增长 {growth:+.2f}%")
                else:
                    aux_data_lines.append(f"- {name}: {current}元")
        
        aux_data_text = "\n".join(aux_data_lines)
        
        # 构建提示词
        system_prompt = prompt_manager.get_system_prompt(state["industry"])
        analysis_prompt = prompt_manager.get_auxiliary_analysis_prompt()
        
        # 核心指标摘要
        core_summary = state["core_analysis"][:500] if len(state["core_analysis"]) > 500 else state["core_analysis"]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", analysis_prompt)
        ])
        
        llm = get_llm()
        chain = prompt | llm
        
        response = chain.invoke({
            "company_name": state["company_name"],
            "report_period": state["report_period"],
            "auxiliary_indicators_data": aux_data_text,
            "core_indicators_summary": core_summary
        })
        
        state["auxiliary_analysis"] = response.content
        state["llm_calls"] += 1
        
        logger.success("✅ 辅助指标分析完成")
        
    except Exception as e:
        error_msg = f"辅助指标分析失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        state["errors"].append(error_msg)
        state["auxiliary_analysis"] = "分析失败。"
    
    return state


def analyze_specific_indicators_node(state: FinancialReportState) -> FinancialReportState:
    """节点: 分析个性化指标
    
    使用 LLM 分析个性化指标（先导信号）
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("🤖 节点执行: LLM分析个性化指标")
    state["current_step"] = "analyze_specific_indicators"
    state["processing_steps"].append("analyze_specific_indicators")
    
    if not state["specific_indicators"]:
        logger.info("ℹ️ 无个性化指标数据")
        state["specific_analysis"] = "无适用的个性化指标数据。"
        return state
    
    try:
        # 准备个性化指标数据文本
        specific_data_lines = []
        business_type = "通用"
        
        for key, value in state["specific_indicators"].items():
            name = value.get("name", key)
            current = value.get("display_format", "N/A")
            change = value.get("change_rate")
            
            if key == "contract_liability":
                business_type = "订阅制/SaaS"
            elif key == "inventory":
                business_type = "硬件/算力"
            
            if change is not None:
                specific_data_lines.append(f"- {name}: {current}元，变化 {change:+.2f}%")
            else:
                specific_data_lines.append(f"- {name}: {current}元")
        
        specific_data_text = "\n".join(specific_data_lines)
        
        # 构建提示词
        system_prompt = prompt_manager.get_system_prompt(state["industry"])
        analysis_prompt = prompt_manager.get_specific_analysis_prompt()
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", analysis_prompt)
        ])
        
        llm = get_llm()
        chain = prompt | llm
        
        response = chain.invoke({
            "company_name": state["company_name"],
            "report_period": state["report_period"],
            "business_type": business_type,
            "specific_indicators_data": specific_data_text
        })
        
        state["specific_analysis"] = response.content
        state["llm_calls"] += 1
        
        logger.success("✅ 个性化指标分析完成")
        
    except Exception as e:
        error_msg = f"个性化指标分析失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        state["warnings"].append(error_msg)
        state["specific_analysis"] = "分析失败。"
    
    return state

