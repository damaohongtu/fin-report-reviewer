"""财报点评系统 - Streamlit 前端界面

简洁大气的财报点评应用界面
"""
import sys
import os
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List

import streamlit as st
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.analysis.report_generator import ReportGenerator
from src.config.industry_configs import industry_config_manager

# ==================== 页面配置 ====================

st.set_page_config(
    page_title="财报点评系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 自定义样式 ====================

st.markdown("""
<style>
    /* 全局样式 */
    .main {
        padding: 2rem;
    }
    
    /* 标题样式 */
    .title-container {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .title-container h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .title-container p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* 侧边栏样式 */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    /* 按钮样式 */
    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
    }
    
    /* 下载按钮样式 */
    .stDownloadButton > button {
        width: 100%;
        background: linear-gradient(135deg, #56ab2f 0%, #a8e063 100%);
        color: white;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 8px;
    }
    
    /* 报告预览样式 */
    .report-preview {
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin: 1rem 0;
    }
    
    /* 指标卡片样式 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        text-align: center;
    }
    
    /* 成功提示样式 */
    .stSuccess {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 5px;
    }
    
    /* 错误提示样式 */
    .stError {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 5px;
    }
    
    /* 信息提示样式 */
    .stInfo {
        background-color: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== 数据配置 ====================

# 公司列表配置（可从数据库或配置文件读取）
COMPANIES = {
    "三六零": {
        "code": "601360",
        "industry": "computer",
        "display_name": "三六零 (601360)"
    },
    "海康威视": {
        "code": "002415",
        "industry": "computer",
        "display_name": "海康威视 (002415)"
    },
    "科大讯飞": {
        "code": "002230",
        "industry": "computer",
        "display_name": "科大讯飞 (002230)"
    },
    "用友网络": {
        "code": "600588",
        "industry": "computer",
        "display_name": "用友网络 (600588)"
    },
}

# 报告期类型
PERIOD_TYPES = {
    "一季报": "Q1",
    "半年报": "Q2",
    "三季报": "Q3",
    "年报": "Q4"
}

# ==================== 辅助函数 ====================

def generate_period_options(year: int, period_type: str) -> str:
    """生成报告期字符串"""
    period_map = {
        "Q1": f"{year}-03-31",
        "Q2": f"{year}-06-30",
        "Q3": f"{year}-09-30",
        "Q4": f"{year}-12-31"
    }
    return period_map.get(period_type, f"{year}-12-31")

def format_processing_time(seconds: float) -> str:
    """格式化处理时间"""
    if seconds < 60:
        return f"{seconds:.1f} 秒"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes} 分 {secs:.1f} 秒"

def save_report_to_file(report: str, company_name: str, report_period: str) -> Path:
    """保存报告到文件"""
    reports_dir = Path("data/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{company_name}_{report_period}_财报点评.md"
    filepath = reports_dir / filename
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    
    return filepath

# ==================== 初始化 Session State ====================

if "report_generated" not in st.session_state:
    st.session_state.report_generated = False
if "report_data" not in st.session_state:
    st.session_state.report_data = None
if "generator" not in st.session_state:
    st.session_state.generator = None

# ==================== 主界面 ====================

def main():
    """主应用函数"""
    
    # 标题栏
    st.markdown("""
    <div class="title-container">
        <h1>📊 财报点评系统</h1>
        <p>基于 LangGraph + DeepSeek 的智能财务分析平台</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.header("⚙️ 配置选项")
        
        # 公司选择
        st.subheader("1️⃣ 选择公司")
        company_options = [info["display_name"] for info in COMPANIES.values()]
        selected_company_display = st.selectbox(
            "公司名称",
            options=company_options,
            help="选择要分析的上市公司"
        )
        
        # 获取选中公司的详细信息
        selected_company = None
        for name, info in COMPANIES.items():
            if info["display_name"] == selected_company_display:
                selected_company = name
                company_info = info
                break
        
        # 显示公司信息
        if selected_company:
            st.info(f"📌 **股票代码**: {company_info['code']}\n\n📍 **所属行业**: {company_info['industry']}")
        
        st.divider()
        
        # 报告期选择
        st.subheader("2️⃣ 选择报告期")
        
        col1, col2 = st.columns(2)
        with col1:
            report_year = st.selectbox(
                "年份",
                options=list(range(2025, 2019, -1)),
                help="选择财报年份"
            )
        
        with col2:
            period_type = st.selectbox(
                "期间",
                options=list(PERIOD_TYPES.keys()),
                help="选择报告期类型"
            )
        
        report_period = generate_period_options(report_year, PERIOD_TYPES[period_type])
        st.success(f"✅ 报告期: **{report_period}**")
        
        st.divider()
        
        # 高级选项
        with st.expander("🔧 高级选项", expanded=False):
            report_type = st.radio(
                "报表类型",
                options=["合并报表 (A)", "母公司报表 (B)"],
                index=0
            )
            report_type_code = "A" if "合并" in report_type else "B"
            
            st.caption("💡 通常选择合并报表进行分析")
        
        st.divider()
        
        # 生成按钮
        generate_button = st.button(
            "🚀 生成财报点评",
            type="primary",
            use_container_width=True
        )
    
    # ==================== 主内容区 ====================
    
    # 如果点击生成按钮
    if generate_button:
        st.session_state.report_generated = False
        st.session_state.report_data = None
        
        # 显示生成进度
        with st.spinner(""):
            progress_container = st.container()
            with progress_container:
                st.info("🔄 正在初始化财报分析引擎...")
                
                try:
                    # 初始化生成器
                    if st.session_state.generator is None:
                        st.session_state.generator = ReportGenerator()
                    
                    generator = st.session_state.generator
                    
                    st.info(f"📊 正在分析 **{selected_company}** 的 **{report_period}** 期财报...")
                    
                    # 生成报告
                    result = generator.generate_report(
                        company_name=selected_company,
                        company_code=company_info["code"],
                        report_period=report_period,
                        industry=company_info["industry"],
                        report_type=report_type_code
                    )
                    
                    # 保存结果
                    st.session_state.report_data = result
                    st.session_state.report_generated = True
                    
                    # 清除进度提示
                    progress_container.empty()
                    
                    # 显示成功消息
                    st.success(f"✅ 财报点评生成成功！耗时: {format_processing_time(result['processing_time'])}")
                    
                except Exception as e:
                    logger.error(f"生成报告失败: {e}")
                    st.error(f"❌ 生成报告失败: {str(e)}")
                    st.session_state.report_generated = False
    
    # 显示报告内容
    if st.session_state.report_generated and st.session_state.report_data:
        result = st.session_state.report_data
        
        # 报告元数据
        st.divider()
        
        # 显示关键指标（如果有）
        if result.get("indicators"):
            st.subheader("📈 关键财务指标")
            
            indicators = result["indicators"]
            core_indicators = indicators.get("core", {})
            
            if core_indicators:
                cols = st.columns(min(4, len(core_indicators)))
                
                for idx, (key, value) in enumerate(core_indicators.items()):
                    with cols[idx % len(cols)]:
                        name = value.get("name", key)
                        current = value.get("display_format", "N/A")
                        growth = value.get("growth_rate")
                        
                        if growth is not None:
                            st.metric(
                                label=name,
                                value=current,
                                delta=f"{growth:+.2f}%"
                            )
                        else:
                            st.metric(label=name, value=current)
        
        st.divider()
        
        # 报告预览和下载
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.subheader("📄 财报点评报告")
        
        with col2:
            # 下载按钮
            report_content = result.get("report", "")
            if report_content:
                st.download_button(
                    label="📥 下载报告",
                    data=report_content,
                    file_name=f"{selected_company}_{report_period}_财报点评.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        
        # 报告内容显示
        if result.get("success"):
            with st.container():
                st.markdown('<div class="report-preview">', unsafe_allow_html=True)
                st.markdown(result.get("report", "无报告内容"))
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.error("⚠️ 报告生成过程中出现错误，请检查日志")
            if result.get("errors"):
                with st.expander("查看错误详情"):
                    for error in result["errors"]:
                        st.code(error)
        
        # 报告质量评分
        if result.get("quality_score") is not None:
            st.divider()
            quality_score = result["quality_score"]
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader("⭐ 报告质量评分")
            with col2:
                st.metric("评分", f"{quality_score}/100")
            
            if result.get("quality_issues"):
                with st.expander("查看质量问题"):
                    for issue in result["quality_issues"]:
                        st.warning(f"• {issue}")
        
        # 处理详情
        with st.expander("🔍 查看处理详情"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**处理步骤:**")
                for step in result.get("processing_steps", []):
                    st.text(f"✓ {step}")
            
            with col2:
                st.markdown("**调用的工具:**")
                for tool in result.get("tools_called", []):
                    st.text(f"🔧 {tool}")
    
    else:
        # 欢迎界面
        st.info("""
        ### 👋 欢迎使用财报点评系统
        
        **使用步骤:**
        1. 在左侧选择要分析的公司
        2. 选择财报年份和期间
        3. 点击"生成财报点评"按钮
        4. 等待系统分析完成
        5. 查看报告并下载
        
        **系统特点:**
        - ✨ 基于 LangGraph 工作流编排
        - 🤖 使用 DeepSeek 大模型分析
        - 📊 自动计算客观财务指标
        - 📈 结合非结构化财报数据
        - 📝 生成专业的 Markdown 格式报告
        """)
        
        # 显示示例
        st.divider()
        st.subheader("📚 功能预览")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            **🎯 核心指标分析**
            - 营业收入增速
            - 净利润增速
            - 归母净利润变化
            """)
        
        with col2:
            st.markdown("""
            **📊 辅助指标分析**
            - 毛利率分析
            - 研发费用率
            - 销售费用率
            """)
        
        with col3:
            st.markdown("""
            **🔍 个性化指标**
            - 合同负债变化
            - 存货环比变化
            - 行业特定指标
            """)
    
    # 页脚
    st.divider()
    st.markdown("""
    <div style="text-align: center; color: #888; padding: 1rem;">
        <p>财报点评系统 v1.0 </p>
    </div>
    """, unsafe_allow_html=True)


# ==================== 启动应用 ====================

if __name__ == "__main__":
    main()

