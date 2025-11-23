"""财报数据HTTP客户端

通过HTTP接口访问财报数据服务，替代直接的数据库连接
"""
from typing import Dict, Optional, List, Any
import requests
from loguru import logger

from src.config.settings import settings


class FinancialDataHttpClient:
    """财报数据HTTP客户端
    
    通过HTTP接口访问独立的财报数据服务
    """
    
    def __init__(self):
        """初始化HTTP客户端"""
        self.base_url = settings.FINANCIAL_DATA_API_URL
        self.timeout = settings.FINANCIAL_DATA_API_TIMEOUT
        
        # 验证服务连接
        self._validate_connection()
    
    def _validate_connection(self):
        """验证财报数据服务连接"""
        try:
            logger.info(f"正在连接财报数据服务: {self.base_url}")
            
            response = requests.get(
                f"{self.base_url}/health",
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.success(f"✅ 财报数据服务连接成功: {data.get('database_type')}")
            else:
                logger.warning(f"⚠️ 财报数据服务返回异常状态码: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 无法连接到财报数据服务: {e}")
            raise ConnectionError(f"财报数据服务连接失败: {self.base_url}")
    
    def get_income_statement(
        self,
        stock_code: str,
        report_period: str,
        report_type: str = "A"
    ) -> Optional[Dict[str, Any]]:
        """获取利润表数据
        
        Args:
            stock_code: 股票代码
            report_period: 报告期
            report_type: 报表类型
            
        Returns:
            利润表数据字典，如果不存在返回None
        """
        try:
            response = requests.post(
                f"{self.base_url}/api/income-statement",
                json={
                    "stock_code": stock_code,
                    "report_period": report_period,
                    "report_type": report_type
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"请求失败 (status={response.status_code}): {response.text}")
            
            result = response.json()
            
            if result.get("success"):
                logger.info(f"✅ 获取利润表数据: {stock_code} {report_period}")
                return result.get("data")
            else:
                logger.warning(f"⚠️ 未找到利润表数据: {stock_code} {report_period}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ 请求超时 (timeout={self.timeout}s)")
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
            response = requests.post(
                f"{self.base_url}/api/balance-sheet",
                json={
                    "stock_code": stock_code,
                    "report_period": report_period,
                    "report_type": report_type
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"请求失败 (status={response.status_code}): {response.text}")
            
            result = response.json()
            
            if result.get("success"):
                logger.info(f"✅ 获取资产负债表数据: {stock_code} {report_period}")
                return result.get("data")
            else:
                logger.warning(f"⚠️ 未找到资产负债表数据: {stock_code} {report_period}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ 请求超时 (timeout={self.timeout}s)")
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
            response = requests.post(
                f"{self.base_url}/api/cash-flow",
                json={
                    "stock_code": stock_code,
                    "report_period": report_period,
                    "report_type": report_type
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"请求失败 (status={response.status_code}): {response.text}")
            
            result = response.json()
            
            if result.get("success"):
                logger.info(f"✅ 获取现金流量表数据: {stock_code} {report_period}")
                return result.get("data")
            else:
                logger.warning(f"⚠️ 未找到现金流量表数据: {stock_code} {report_period}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ 请求超时 (timeout={self.timeout}s)")
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
            response = requests.post(
                f"{self.base_url}/api/historical-periods",
                json={
                    "stock_code": stock_code,
                    "current_period": current_period,
                    "count": count
                },
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"请求失败 (status={response.status_code}): {response.text}")
            
            result = response.json()
            
            if result.get("success"):
                periods = result.get("data", [])
                logger.info(f"✅ 获取历史期数: {len(periods)}期")
                return periods
            else:
                return []
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ 请求超时 (timeout={self.timeout}s)")
            return []
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
        try:
            response = requests.post(
                f"{self.base_url}/api/complete-data",
                json={
                    "stock_code": stock_code,
                    "report_period": report_period,
                    "report_type": report_type,
                    "include_previous": include_previous
                },
                timeout=self.timeout * 2  # 完整数据查询可能需要更长时间
            )
            
            if response.status_code != 200:
                raise RuntimeError(f"请求失败 (status={response.status_code}): {response.text}")
            
            result = response.json()
            
            if result.get("success"):
                logger.success(f"✅ 获取完整财务数据: {stock_code} {report_period}")
                return result.get("data", {})
            else:
                logger.warning(f"⚠️ 获取完整财务数据失败")
                return {}
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ 请求超时")
            return {}
        except Exception as e:
            logger.error(f"❌ 获取完整财务数据失败: {e}")
            return {}
    
    def close(self):
        """关闭连接（HTTP客户端无需显式关闭）"""
        logger.info("财报数据HTTP客户端已关闭")

