"""
财报数据 HTTP 服务

提供HTTP接口的财报数据查询服务，封装PostgreSQL数据库访问
使用FastAPI实现

启动方式：
python financial-data-service/financial_data_server.py --host 0.0.0.0 --port 8081 --database-url postgresql://postgres:postgres@localhost:5432/financial_reports
或使用uvicorn：
uvicorn financial_data_server:app --host 0.0.0.0 --port 8081 --database-url postgresql://postgres:postgres@localhost:5432/financial_reports

参数说明：
--host: 服务host (默认: 0.0.0.0)
--port: 服务端口 (默认: 8081)
--database-url: 数据库连接URL (必需)
--reload: 开启热重载，用于开发模式
"""

import argparse
import os
from typing import Dict, Optional, List, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from loguru import logger

# ==================== 配置 ====================
DEFAULT_PORT = 8081
DEFAULT_HOST = "0.0.0.0"

# ==================== API模型 ====================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    database: str = Field(..., description="数据库连接状态")
    database_type: str = Field(..., description="数据库类型")

class IncomeStatementRequest(BaseModel):
    """利润表查询请求"""
    stock_code: str = Field(..., description="股票代码", json_schema_extra={"example": "000001"})
    report_period: str = Field(..., description="报告期", json_schema_extra={"example": "2024-03-31"})
    report_type: str = Field(default="A", description="报表类型 A=合并报表 B=母公司报表")

class BalanceSheetRequest(BaseModel):
    """资产负债表查询请求"""
    stock_code: str = Field(..., description="股票代码", json_schema_extra={"example": "000001"})
    report_period: str = Field(..., description="报告期", json_schema_extra={"example": "2024-03-31"})
    report_type: str = Field(default="A", description="报表类型 A=合并报表 B=母公司报表")

class CashFlowRequest(BaseModel):
    """现金流量表查询请求"""
    stock_code: str = Field(..., description="股票代码", json_schema_extra={"example": "000001"})
    report_period: str = Field(..., description="报告期", json_schema_extra={"example": "2024-03-31"})
    report_type: str = Field(default="A", description="报表类型 A=合并报表 B=母公司报表")

class HistoricalPeriodsRequest(BaseModel):
    """历史期查询请求"""
    stock_code: str = Field(..., description="股票代码", json_schema_extra={"example": "000001"})
    current_period: str = Field(..., description="当前报告期", json_schema_extra={"example": "2024-03-31"})
    count: int = Field(default=4, description="获取历史期数", ge=1, le=20)

class CompleteDataRequest(BaseModel):
    """完整财务数据查询请求"""
    stock_code: str = Field(..., description="股票代码", json_schema_extra={"example": "000001"})
    report_period: str = Field(..., description="报告期", json_schema_extra={"example": "2024-03-31"})
    report_type: str = Field(default="A", description="报表类型")
    include_previous: bool = Field(default=True, description="是否包含上期数据")

# ==================== FastAPI应用 ====================

# 全局变量
db_engine: Optional[Engine] = None
database_url: str = ""

def init_database(db_url: str):
    """初始化数据库连接"""
    global db_engine, database_url
    
    try:
        logger.info(f"正在连接数据库...")
        logger.info(f"数据库URL: {db_url.split('@')[-1]}")  # 只显示地址部分，隐藏密码
        
        db_engine = create_engine(
            db_url,
            echo=False,
            pool_pre_ping=True,  # 连接池健康检查
            pool_recycle=3600  # 1小时回收连接
        )
        
        # 测试连接
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        database_url = db_url
        logger.success(f"✅ 数据库连接成功")
        
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 财报数据服务启动中...")

    # uvicorn 以字符串模块路径启动时会重新导入本模块，
    # db_engine 全局变量在新模块实例中为 None。
    # 通过环境变量传递数据库 URL，在 lifespan 中完成初始化。
    if db_engine is None:
        db_url = os.environ.get("FIN_DATA_DB_URL", "")
        if db_url:
            init_database(db_url)
        else:
            logger.warning("⚠️ 数据库未初始化，请通过 --database-url 参数指定连接地址")

    yield

    # Shutdown: 关闭数据库连接
    if db_engine:
        db_engine.dispose()
        logger.info("🛑 数据库连接已关闭")

app = FastAPI(
    title="Financial Data Service",
    description="提供财报数据查询服务",
    version="1.0.0",
    lifespan=lifespan
)

# ==================== API端点 ====================

@app.get("/", summary="服务信息")
async def root():
    """根路径"""
    return {
        "service": "Financial Data Service",
        "version": "1.0.0",
        "database": "connected" if db_engine else "not connected",
        "endpoints": {
            "health": "/health",
            "income_statement": "/api/income-statement",
            "balance_sheet": "/api/balance-sheet",
            "cash_flow": "/api/cash-flow",
            "historical_periods": "/api/historical-periods",
            "complete_data": "/api/complete-data",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """健康检查"""
    if db_engine is None:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    try:
        with db_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        # 判断数据库类型
        db_type = "postgresql" if "postgresql" in database_url else "unknown"
        
        return HealthResponse(
            status="healthy",
            database="connected",
            database_type=db_type
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"数据库连接异常: {str(e)}")

@app.post("/api/income-statement", summary="查询利润表")
async def get_income_statement(request: IncomeStatementRequest) -> Dict[str, Any]:
    """获取利润表数据"""
    if db_engine is None:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    try:
        query = text("""
            SELECT 
                stkcd, accper, typrep, short_name,
                b001101000 as revenue,
                b001201000 as cost,
                b001207000 as business_tax,
                b001209000 as sales_expense,
                b001210000 as admin_expense,
                b001216000 as rd_expense,
                b001211000 as finance_expense,
                b001211101 as interest_expense,
                b001300000 as operating_profit,
                b001000000 as total_profit,
                b002000000 as net_profit,
                b002000101 as net_profit_parent
            FROM ashare.a_share_income_statement
            WHERE stkcd = :stock_code
                AND accper = :report_period
                AND typrep = :report_type
            LIMIT 1
        """)
        
        with db_engine.connect() as conn:
            result = conn.execute(
                query,
                {
                    "stock_code": request.stock_code,
                    "report_period": request.report_period,
                    "report_type": request.report_type
                }
            ).fetchone()
            
            if result:
                data = dict(result._mapping)
                logger.info(f"✅ 查询利润表: {request.stock_code} {request.report_period}")
                return {"success": True, "data": data}
            else:
                logger.warning(f"⚠️ 未找到数据: {request.stock_code} {request.report_period}")
                return {"success": False, "data": None, "message": "未找到数据"}
                
    except Exception as e:
        logger.error(f"❌ 查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.post("/api/balance-sheet", summary="查询资产负债表")
async def get_balance_sheet(request: BalanceSheetRequest) -> Dict[str, Any]:
    """获取资产负债表数据"""
    if db_engine is None:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    try:
        query = text("""
            SELECT 
                stkcd, accper, typrep, short_name,
                a001100000 as current_assets,
                a001200000 as non_current_assets,
                a001000000 as total_assets,
                a002100000 as current_liabilities,
                a002200000 as non_current_liabilities,
                a002000000 as total_liabilities,
                a003000000 as total_equity,
                a003100000 as parent_equity,
                a001123000 as inventory,
                a002128000 as contract_liability,
                a001212000 as fixed_assets,
                a001107000 as trading_financial_assets,
                a001202000 as available_for_sale_assets,
                a001203000 as held_to_maturity_investments,
                a001205000 as long_term_equity_investment,
                a001226000 as debt_investments,
                a001228000 as other_equity_instruments_invest,
                a001229000 as other_noncurrent_financial_assets,
                a002101000 as short_term_borrowing,
                a002105000 as trading_financial_liabilities,
                a002125000 as current_noncurrent_liabilities,
                a002201000 as long_term_borrowing,
                a002203000 as bonds_payable,
                a002211000 as lease_liabilities
            FROM ashare.a_share_balance_sheet
            WHERE stkcd = :stock_code
                AND accper = :report_period
                AND typrep = :report_type
            LIMIT 1
        """)
        
        with db_engine.connect() as conn:
            result = conn.execute(
                query,
                {
                    "stock_code": request.stock_code,
                    "report_period": request.report_period,
                    "report_type": request.report_type
                }
            ).fetchone()
            
            if result:
                data = dict(result._mapping)
                logger.info(f"✅ 查询资产负债表: {request.stock_code} {request.report_period}")
                return {"success": True, "data": data}
            else:
                return {"success": False, "data": None, "message": "未找到数据"}
                
    except Exception as e:
        logger.error(f"❌ 查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.post("/api/cash-flow", summary="查询现金流量表")
async def get_cash_flow(request: CashFlowRequest) -> Dict[str, Any]:
    """获取现金流量表数据"""
    if db_engine is None:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    try:
        query = text("""
            SELECT 
                stkcd, accper, typrep, short_name,
                c001100000 as operating_cash_inflow,
                c001200000 as operating_cash_outflow,
                c001000000 as net_operating_cash_flow,
                c002100000 as investing_cash_inflow,
                c002200000 as investing_cash_outflow,
                c002000000 as net_investing_cash_flow,
                c003100000 as financing_cash_inflow,
                c003200000 as financing_cash_outflow,
                c003000000 as net_financing_cash_flow,
                c005000000 as net_cash_increase
            FROM ashare.a_share_cashflow_statement
            WHERE stkcd = :stock_code
                AND accper = :report_period
                AND typrep = :report_type
            LIMIT 1
        """)
        
        with db_engine.connect() as conn:
            result = conn.execute(
                query,
                {
                    "stock_code": request.stock_code,
                    "report_period": request.report_period,
                    "report_type": request.report_type
                }
            ).fetchone()
            
            if result:
                data = dict(result._mapping)
                logger.info(f"✅ 查询现金流量表: {request.stock_code} {request.report_period}")
                return {"success": True, "data": data}
            else:
                return {"success": False, "data": None, "message": "未找到数据"}
                
    except Exception as e:
        logger.error(f"❌ 查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.post("/api/historical-periods", summary="查询历史期")
async def get_historical_periods(request: HistoricalPeriodsRequest) -> Dict[str, Any]:
    """获取历史报告期列表"""
    if db_engine is None:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    try:
        query = text("""
            SELECT DISTINCT accper
            FROM ashare.a_share_income_statement
            WHERE stkcd = :stock_code
                AND accper < :current_period
            ORDER BY accper DESC
            LIMIT :count
        """)
        
        with db_engine.connect() as conn:
            results = conn.execute(
                query,
                {
                    "stock_code": request.stock_code,
                    "current_period": request.current_period,
                    "count": request.count
                }
            ).fetchall()
            
            periods = [str(row[0]) for row in results]
            logger.info(f"✅ 查询历史期: {request.stock_code}, 共{len(periods)}期")
            return {"success": True, "data": periods}
                
    except Exception as e:
        logger.error(f"❌ 查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

@app.post("/api/complete-data", summary="查询完整财务数据")
async def get_complete_data(request: CompleteDataRequest) -> Dict[str, Any]:
    """获取完整的财务数据（三张表 + 上期数据）"""
    if db_engine is None:
        raise HTTPException(status_code=503, detail="数据库未连接")
    
    try:
        result = {
            "stock_code": request.stock_code,
            "report_period": request.report_period,
            "report_type": request.report_type,
            "income_statement": None,
            "balance_sheet": None,
            "cash_flow": None,
            "previous_period": None,
            "previous_data": None
        }
        
        # 获取当期三张表
        income_resp = await get_income_statement(
            IncomeStatementRequest(
                stock_code=request.stock_code,
                report_period=request.report_period,
                report_type=request.report_type
            )
        )
        result["income_statement"] = income_resp.get("data")
        
        balance_resp = await get_balance_sheet(
            BalanceSheetRequest(
                stock_code=request.stock_code,
                report_period=request.report_period,
                report_type=request.report_type
            )
        )
        result["balance_sheet"] = balance_resp.get("data")
        
        cash_resp = await get_cash_flow(
            CashFlowRequest(
                stock_code=request.stock_code,
                report_period=request.report_period,
                report_type=request.report_type
            )
        )
        result["cash_flow"] = cash_resp.get("data")
        
        # 获取上期数据
        if request.include_previous:
            historical_resp = await get_historical_periods(
                HistoricalPeriodsRequest(
                    stock_code=request.stock_code,
                    current_period=request.report_period,
                    count=1
                )
            )
            
            if historical_resp.get("success") and historical_resp.get("data"):
                previous_period = historical_resp["data"][0]
                result["previous_period"] = previous_period
                
                # 获取上期三张表
                prev_income = await get_income_statement(
                    IncomeStatementRequest(
                        stock_code=request.stock_code,
                        report_period=previous_period,
                        report_type=request.report_type
                    )
                )
                prev_balance = await get_balance_sheet(
                    BalanceSheetRequest(
                        stock_code=request.stock_code,
                        report_period=previous_period,
                        report_type=request.report_type
                    )
                )
                prev_cash = await get_cash_flow(
                    CashFlowRequest(
                        stock_code=request.stock_code,
                        report_period=previous_period,
                        report_type=request.report_type
                    )
                )
                
                result["previous_data"] = {
                    "income_statement": prev_income.get("data"),
                    "balance_sheet": prev_balance.get("data"),
                    "cash_flow": prev_cash.get("data")
                }
        
        logger.success(f"✅ 获取完整财务数据: {request.stock_code} {request.report_period}")
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"❌ 获取完整数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")

# ==================== 命令行启动 ====================

def main():
    """命令行启动"""
    parser = argparse.ArgumentParser(description="财报数据 HTTP 服务")
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="服务host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="服务端口")
    parser.add_argument("--database-url", type=str, required=True, help="数据库连接URL")
    parser.add_argument("--reload", action="store_true", help="开启热重载（开发模式）")

    args = parser.parse_args()

    # 将数据库 URL 写入环境变量，供 lifespan 在 uvicorn 子进程中读取
    os.environ["FIN_DATA_DB_URL"] = args.database_url

    import uvicorn

    logger.info(f"🚀 启动财报数据服务: {args.host}:{args.port}")

    uvicorn.run(
        "financial_data_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()

