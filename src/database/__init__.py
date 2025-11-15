"""数据库模块（已弃用，改用HTTP客户端）"""
# 保留向后兼容，但推荐使用 src.clients.FinancialDataHttpClient
from src.database.financial_data_service import FinancialDataService

__all__ = ["FinancialDataService"]

# 推荐使用HTTP客户端：
# from src.clients import FinancialDataHttpClient

