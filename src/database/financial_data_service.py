"""财务数据服务

从PostgreSQL数据库获取结构化的财报数据
"""
from typing import Dict, Optional, List, Any
from datetime import datetime
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config.settings import settings


class FinancialDataService:
    """财务数据服务"""
    
    def __init__(self):
        """初始化数据库连接"""
        self.engine: Optional[Engine] = None
        self._connect()
    
    def _connect(self):
        """连接数据库"""
        try:
            self.engine = create_engine(
                settings.DATABASE_URL,
                echo=settings.DATABASE_ECHO,
                pool_pre_ping=True,  # 连接池健康检查
                pool_recycle=3600  # 1小时回收连接
            )
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.success(f"✅ 数据库连接成功: {settings.DATABASE_URL.split('@')[-1]}")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    def get_income_statement(
        self,
        stock_code: str,
        report_period: str,
        report_type: str = "A"
    ) -> Optional[Dict[str, Any]]:
        """获取利润表数据
        
        Args:
            stock_code: 股票代码，如 "000001"
            report_period: 报告期，如 "2024-03-31"
            report_type: 报表类型，A=合并报表，B=母公司报表
            
        Returns:
            利润表数据字典，如果不存在返回None
        """
        try:
            query = text("""
                SELECT 
                    stkcd,
                    accper,
                    typrep,
                    short_name,
                    -- 营业收入
                    b001101000 as revenue,
                    -- 营业成本
                    b001201000 as cost,
                    -- 税金及附加
                    b001207000 as business_tax,
                    -- 销售费用
                    b001209000 as sales_expense,
                    -- 管理费用
                    b001210000 as admin_expense,
                    -- 研发费用
                    b001216000 as rd_expense,
                    -- 财务费用
                    b001211000 as finance_expense,
                    -- 营业利润
                    b001300000 as operating_profit,
                    -- 利润总额
                    b001000000 as total_profit,
                    -- 净利润
                    b002000000 as net_profit,
                    -- 归属于母公司所有者的净利润
                    b002000101 as net_profit_parent
                FROM ashare.a_share_income_statement
                WHERE stkcd = :stock_code
                    AND accper = :report_period
                    AND typrep = :report_type
                LIMIT 1
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {
                        "stock_code": stock_code,
                        "report_period": report_period,
                        "report_type": report_type
                    }
                ).fetchone()
                
                if result:
                    # 转换为字典
                    data = dict(result._mapping)
                    logger.info(f"✅ 获取利润表数据: {stock_code} {report_period}")
                    return data
                else:
                    logger.warning(f"⚠️ 未找到利润表数据: {stock_code} {report_period}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ 获取利润表数据失败: {e}")
            return None
    
    def get_balance_sheet(
        self,
        stock_code: str,
        report_period: str,
        report_type: str = "A"
    ) -> Optional[Dict[str, Any]]:
        """获取资产负债表数据
        
        Args:
            stock_code: 股票代码
            report_period: 报告期
            report_type: 报表类型
            
        Returns:
            资产负债表数据字典
        """
        try:
            query = text("""
                SELECT 
                    stkcd,
                    accper,
                    typrep,
                    short_name,
                    -- 资产
                    a001100000 as current_assets,
                    a001200000 as non_current_assets,
                    a001000000 as total_assets,
                    -- 负债
                    a002100000 as current_liabilities,
                    a002200000 as non_current_liabilities,
                    a002000000 as total_liabilities,
                    -- 股东权益
                    a003000000 as total_equity,
                    a003100000 as parent_equity,
                    -- 特殊项目
                    a001123000 as inventory,  -- 存货
                    a002128000 as contract_liability  -- 合同负债
                FROM ashare.a_share_balance_sheet
                WHERE stkcd = :stock_code
                    AND accper = :report_period
                    AND typrep = :report_type
                LIMIT 1
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {
                        "stock_code": stock_code,
                        "report_period": report_period,
                        "report_type": report_type
                    }
                ).fetchone()
                
                if result:
                    data = dict(result._mapping)
                    logger.info(f"✅ 获取资产负债表数据: {stock_code} {report_period}")
                    return data
                else:
                    logger.warning(f"⚠️ 未找到资产负债表数据: {stock_code} {report_period}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ 获取资产负债表数据失败: {e}")
            return None
    
    def get_cash_flow(
        self,
        stock_code: str,
        report_period: str,
        report_type: str = "A"
    ) -> Optional[Dict[str, Any]]:
        """获取现金流量表数据
        
        Args:
            stock_code: 股票代码
            report_period: 报告期
            report_type: 报表类型
            
        Returns:
            现金流量表数据字典
        """
        try:
            query = text("""
                SELECT 
                    stkcd,
                    accper,
                    typrep,
                    short_name,
                    -- 经营活动现金流
                    c001100000 as operating_cash_inflow,
                    c001200000 as operating_cash_outflow,
                    c001000000 as net_operating_cash_flow,
                    -- 投资活动现金流
                    c002100000 as investing_cash_inflow,
                    c002200000 as investing_cash_outflow,
                    c002000000 as net_investing_cash_flow,
                    -- 筹资活动现金流
                    c003100000 as financing_cash_inflow,
                    c003200000 as financing_cash_outflow,
                    c003000000 as net_financing_cash_flow,
                    -- 现金净增加额
                    c005000000 as net_cash_increase
                FROM ashare.a_share_cashflow_statement
                WHERE stkcd = :stock_code
                    AND accper = :report_period
                    AND typrep = :report_type
                LIMIT 1
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(
                    query,
                    {
                        "stock_code": stock_code,
                        "report_period": report_period,
                        "report_type": report_type
                    }
                ).fetchone()
                
                if result:
                    data = dict(result._mapping)
                    logger.info(f"✅ 获取现金流量表数据: {stock_code} {report_period}")
                    return data
                else:
                    logger.warning(f"⚠️ 未找到现金流量表数据: {stock_code} {report_period}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ 获取现金流量表数据失败: {e}")
            return None
    
    def get_historical_periods(
        self,
        stock_code: str,
        current_period: str,
        count: int = 4
    ) -> List[str]:
        """获取历史报告期列表
        
        Args:
            stock_code: 股票代码
            current_period: 当前报告期
            count: 获取历史期数
            
        Returns:
            历史报告期列表（降序）
        """
        try:
            query = text("""
                SELECT DISTINCT accper
                FROM ashare.a_share_income_statement
                WHERE stkcd = :stock_code
                    AND accper < :current_period
                ORDER BY accper DESC
                LIMIT :count
            """)
            
            with self.engine.connect() as conn:
                results = conn.execute(
                    query,
                    {
                        "stock_code": stock_code,
                        "current_period": current_period,
                        "count": count
                    }
                ).fetchall()
                
                periods = [str(row[0]) for row in results]
                logger.info(f"✅ 获取历史期数: {len(periods)}期")
                return periods
                
        except Exception as e:
            logger.error(f"❌ 获取历史期数失败: {e}")
            return []
    
    def get_complete_financial_data(
        self,
        stock_code: str,
        report_period: str,
        report_type: str = "A",
        include_previous: bool = True
    ) -> Dict[str, Any]:
        """获取完整的财务数据（三张表）
        
        Args:
            stock_code: 股票代码
            report_period: 报告期
            report_type: 报表类型
            include_previous: 是否包含上期数据
            
        Returns:
            包含三张表的完整数据
        """
        result = {
            "stock_code": stock_code,
            "report_period": report_period,
            "report_type": report_type,
            "income_statement": None,
            "balance_sheet": None,
            "cash_flow": None,
            "previous_period": None,
            "previous_data": None
        }
        
        # 获取当期数据
        result["income_statement"] = self.get_income_statement(
            stock_code, report_period, report_type
        )
        result["balance_sheet"] = self.get_balance_sheet(
            stock_code, report_period, report_type
        )
        result["cash_flow"] = self.get_cash_flow(
            stock_code, report_period, report_type
        )
        
        # 获取上期数据
        if include_previous:
            historical = self.get_historical_periods(stock_code, report_period, count=1)
            if historical:
                previous_period = historical[0]
                result["previous_period"] = previous_period
                result["previous_data"] = {
                    "income_statement": self.get_income_statement(
                        stock_code, previous_period, report_type
                    ),
                    "balance_sheet": self.get_balance_sheet(
                        stock_code, previous_period, report_type
                    ),
                    "cash_flow": self.get_cash_flow(
                        stock_code, previous_period, report_type
                    )
                }
        
        logger.success(f"✅ 获取完整财务数据: {stock_code} {report_period}")
        return result
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")

