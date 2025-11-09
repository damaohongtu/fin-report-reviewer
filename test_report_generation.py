#!/usr/bin/env python3
"""测试报告生成功能

基于 LangGraph 工作流测试完整的报告生成流程：
1. 获取财务数据（PostgreSQL）
2. 计算技术指标（Tools）
3. 检索上下文（Milvus）
4. LLM分析（核心、辅助、个性化指标）
5. 生成最终报告
6. 质量检查
"""
import sys
from pathlib import Path
from loguru import logger

from src.analysis.report_generator import ReportGenerator
from src.config.settings import settings


def setup_logger():
    """配置日志"""
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    logger.add(
        "logs/test_report_generation_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="DEBUG"
    )


def test_database_connection():
    """测试1: 数据库连接"""
    logger.info("\n" + "="*60)
    logger.info("测试1: PostgreSQL数据库连接")
    logger.info("="*60)
    
    try:
        from src.database.financial_data_service import FinancialDataService
        
        db_service = FinancialDataService()
        logger.success("✅ 数据库连接成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        logger.info("请检查 DATABASE_URL 配置")
        return False


def test_milvus_connection():
    """测试2: Milvus连接"""
    logger.info("\n" + "="*60)
    logger.info("测试2: Milvus向量数据库连接")
    logger.info("="*60)
    
    try:
        from src.retrieval.vector_retriever import VectorRetriever
        
        retriever = VectorRetriever()
        logger.success("✅ Milvus连接成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ Milvus连接失败: {e}")
        logger.info("请检查 MILVUS_HOST/PORT/USER/PASSWORD 配置")
        return False


def test_financial_data_retrieval():
    """测试3: 财务数据获取"""
    logger.info("\n" + "="*60)
    logger.info("测试3: 获取财务数据（Tool调用）")
    logger.info("="*60)
    
    try:
        from src.tools import get_complete_financial_data_tool
        
        # 测试获取三六零2024Q1财报
        data = get_complete_financial_data_tool.invoke({
            "stock_code": "601360",
            "report_period": "2024-03-31",
            "report_type": "A",
            "include_previous": True
        })
        
        if data and data.get("income_statement"):
            logger.success("✅ 财务数据获取成功")
            logger.info(f"  利润表: {'有' if data.get('income_statement') else '无'}")
            logger.info(f"  资产负债表: {'有' if data.get('balance_sheet') else '无'}")
            logger.info(f"  现金流量表: {'有' if data.get('cash_flow') else '无'}")
            logger.info(f"  上期数据: {data.get('previous_period', '无')}")
            return True
        else:
            logger.warning("⚠️ 未找到财务数据")
            logger.info("请确保数据库中有 601360 (三六零) 2024-03-31 期的数据")
            return False
            
    except Exception as e:
        logger.error(f"❌ 财务数据获取失败: {e}")
        logger.exception(e)
        return False


def test_indicator_calculation():
    """测试4: 指标计算"""
    logger.info("\n" + "="*60)
    logger.info("测试4: 计算技术指标（Tool调用）")
    logger.info("="*60)
    
    try:
        from src.tools import get_complete_financial_data_tool, calculate_all_indicators_tool
        
        # 获取数据
        data = get_complete_financial_data_tool.invoke({
            "stock_code": "601360",
            "report_period": "2024-03-31",
            "report_type": "A",
            "include_previous": True
        })
        
        if not data or not data.get("income_statement"):
            logger.warning("⚠️ 无财务数据，跳过指标计算测试")
            return False
        
        # 计算指标
        current_data = {
            "income_statement": data.get("income_statement"),
            "balance_sheet": data.get("balance_sheet"),
            "cash_flow": data.get("cash_flow")
        }
        
        indicators = calculate_all_indicators_tool.invoke({
            "industry": "computer",
            "current_data": current_data,
            "previous_data": data.get("previous_data")
        })
        
        logger.success("✅ 指标计算完成")
        logger.info(f"  核心指标: {len(indicators.get('core', {}))}个")
        logger.info(f"  辅助指标: {len(indicators.get('auxiliary', {}))}个")
        logger.info(f"  个性化指标: {len(indicators.get('specific', {}))}个")
        
        # 显示部分指标
        if indicators.get('core'):
            logger.info("\n  核心指标示例:")
            for key, value in list(indicators['core'].items())[:2]:
                name = value.get('name', key)
                growth = value.get('growth_rate')
                if growth is not None:
                    logger.info(f"    - {name}: 增长率 {growth:+.2f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 指标计算失败: {e}")
        logger.exception(e)
        return False


def test_milvus_retrieval():
    """测试5: Milvus检索"""
    logger.info("\n" + "="*60)
    logger.info("测试5: Milvus文本检索（Tool调用）")
    logger.info("="*60)
    
    try:
        from src.tools import get_context_for_analysis_tool
        
        context = get_context_for_analysis_tool.invoke({
            "company_name": "三六零",
            "report_period": "2025-03-31",
            "query": None
        })
        
        if context:
            logger.success(f"✅ 检索成功，上下文长度: {len(context)} 字符")
            logger.info(f"  预览: {context[:200]}...")
            return True
        else:
            logger.warning("⚠️ 未检索到数据")
            logger.info("请先运行 test_report_ingestion.py 摄入PDF数据")
            return False
            
    except Exception as e:
        logger.error(f"❌ Milvus检索失败: {e}")
        logger.exception(e)
        return False


def test_langgraph_workflow():
    """测试6: LangGraph工作流"""
    logger.info("\n" + "="*60)
    logger.info("测试6: LangGraph工作流测试")
    logger.info("="*60)
    
    try:
        from src.graphs import create_initial_state, create_financial_report_graph
        
        # 创建工作流
        graph = create_financial_report_graph()
        logger.success("✅ LangGraph工作流创建成功")
        
        # 创建初始状态
        initial_state = create_initial_state(
            company_name="三六零",
            company_code="601360",
            report_period="2024-03-31",
            industry="computer"
        )
        logger.success("✅ 初始状态创建成功")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ LangGraph工作流测试失败: {e}")
        logger.exception(e)
        return False


def test_full_report_generation():
    """测试7: 完整报告生成"""
    logger.info("\n" + "="*60)
    logger.info("测试7: 完整报告生成（LangGraph完整流程）")
    logger.info("="*60)
    
    try:
        # 创建报告生成器
        generator = ReportGenerator()
        logger.info("报告生成器初始化完成")
        
        # 生成报告
        logger.info("开始生成报告...")
        logger.info("  公司: 三六零")
        logger.info("  代码: 601360")
        logger.info("  期间: 2024-03-31")
        logger.info("  行业: computer")
        
        result = generator.generate_report(
            company_name="三六零",
            company_code="601360",
            report_period="2024-03-31",
            industry="computer"
        )
        
        # 检查结果
        if result.get("success"):
            logger.success("✅ 报告生成成功！")
            logger.info(f"\n处理统计:")
            logger.info(f"  处理时间: {result.get('processing_time', 0):.2f}秒")
            logger.info(f"  LLM调用: {result.get('llm_calls', 0)}次")
            logger.info(f"  质量评分: {result.get('quality_score', 0)}")
            logger.info(f"  工具调用: {len(result.get('tools_called', []))}个")
            logger.info(f"  处理步骤: {len(result.get('processing_steps', []))}步")
            
            # 显示报告预览
            report = result.get('report', '')
            if report:
                logger.info(f"\n报告预览（前500字）:")
                logger.info("="*60)
                logger.info(report[:500])
                logger.info("...")
                logger.info("="*60)
                
                # 保存报告
                output_dir = Path("data/reports")
                output_dir.mkdir(parents=True, exist_ok=True)
                
                filename = f"三六零_601360_2024Q1_测试报告.md"
                filepath = output_dir / filename
                
                filepath.write_text(report, encoding='utf-8')
                logger.success(f"✅ 报告已保存: {filepath}")
            
            # 显示错误和警告
            if result.get('errors'):
                logger.warning(f"\n错误: {result['errors']}")
            if result.get('warnings'):
                logger.warning(f"警告: {result['warnings']}")
            
            return True
        else:
            logger.error(f"❌ 报告生成失败")
            logger.error(f"错误: {result.get('error', '未知错误')}")
            if result.get('errors'):
                logger.error(f"详细错误: {result['errors']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 报告生成异常: {e}")
        logger.exception(e)
        return False


def main():
    """主测试函数"""
    setup_logger()
    
    logger.info("\n" + "="*60)
    logger.info("财报点评系统 - 功能测试（基于LangGraph）")
    logger.info("="*60)
    
    # 测试列表
    tests = [
        ("数据库连接", test_database_connection),
        ("Milvus连接", test_milvus_connection),
        ("财务数据获取", test_financial_data_retrieval),
        ("指标计算", test_indicator_calculation),
        ("Milvus检索", test_milvus_retrieval),
        ("LangGraph工作流", test_langgraph_workflow),
        ("完整报告生成", test_full_report_generation),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            logger.exception(f"测试异常: {test_name}")
            results.append((test_name, False))
    
    # 汇总结果
    logger.info("\n" + "="*60)
    logger.info("测试汇总")
    logger.info("="*60)
    
    passed = sum(1 for _, success in results if success)
    failed = len(results) - passed
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\n通过: {passed}/{len(results)}")
    logger.info(f"失败: {failed}/{len(results)}")
    logger.info("="*60)
    
    if failed == 0:
        logger.success("\n🎉 所有测试通过！系统运行正常。")
    else:
        logger.warning(f"\n⚠️ 有 {failed} 个测试失败，请检查配置和数据。")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

