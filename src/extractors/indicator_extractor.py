"""财务指标提取模块

从结构化财报数据中计算客观的技术指标
避免大模型计算导致的GIGO(garbage in garbage out)
"""
from typing import Dict, List, Optional, Any
from decimal import Decimal, InvalidOperation

from loguru import logger

from src.config.industry_configs import IndustryConfig, industry_config_manager


class IndicatorExtractor:
    """财务指标提取器
    
    基于行业配置，从数据库获取的财务数据中计算客观指标
    """
    
    def __init__(self, industry: str):
        """初始化指标提取器
        
        Args:
            industry: 行业名称或代码
        """
        self.industry = industry
        self.config: IndustryConfig = industry_config_manager.get_config(industry)
        logger.info(f"初始化{self.config.name}行业指标提取器")
    
    def extract_indicators(
        self,
        current_data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """从财务数据中提取指标
        
        Args:
            current_data: 当前期数据，包含income_statement、balance_sheet、cash_flow
            previous_data: 上期数据（可选）
            
        Returns:
            按优先级分类的指标字典
        """
        logger.info(f"开始提取{self.config.name}行业关键指标")
        
        result = {
            "industry": self.industry,
            "core": self._extract_core_indicators(current_data, previous_data),
            "auxiliary": self._extract_auxiliary_indicators(current_data, previous_data),
            "specific": self._extract_specific_indicators(current_data, previous_data),
        }
        
        logger.success(f"✅ 指标提取完成")
        return result
    
    def _extract_core_indicators(
        self,
        current_data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取核心指标"""
        indicators = {}
        
        current_income = current_data.get("income_statement", {})
        previous_income = previous_data.get("income_statement", {}) if previous_data else {}
        
        # 1. 营业收入增速
        revenue_current = self._get_value(current_income, "revenue")
        revenue_previous = self._get_value(previous_income, "revenue")
        
        if revenue_current is not None:
            indicators["revenue"] = {
                "name": "营业收入",
                "current": revenue_current,
                "previous": revenue_previous,
                "growth_rate": self._calculate_growth_rate(revenue_current, revenue_previous),
                "unit": "元",
                "display_format": self._format_large_number(revenue_current)
            }
        
        # 2. 净利润增速
        net_profit_current = self._get_value(current_income, "net_profit")
        net_profit_previous = self._get_value(previous_income, "net_profit")
        
        if net_profit_current is not None:
            indicators["net_profit"] = {
                "name": "净利润",
                "current": net_profit_current,
                "previous": net_profit_previous,
                "growth_rate": self._calculate_growth_rate(net_profit_current, net_profit_previous),
                "unit": "元",
                "display_format": self._format_large_number(net_profit_current)
            }
        
        # 3. 归母净利润
        net_profit_parent_current = self._get_value(current_income, "net_profit_parent")
        net_profit_parent_previous = self._get_value(previous_income, "net_profit_parent")
        
        if net_profit_parent_current is not None:
            indicators["net_profit_parent"] = {
                "name": "归母净利润",
                "current": net_profit_parent_current,
                "previous": net_profit_parent_previous,
                "growth_rate": self._calculate_growth_rate(
                    net_profit_parent_current, net_profit_parent_previous
                ),
                "unit": "元",
                "display_format": self._format_large_number(net_profit_parent_current)
            }
        
        return indicators
    
    def _extract_auxiliary_indicators(
        self,
        current_data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取辅助指标"""
        indicators = {}
        
        current_income = current_data.get("income_statement", {})
        previous_income = previous_data.get("income_statement", {}) if previous_data else {}
        
        # 1. 毛利率
        gross_margin_current = self._calculate_gross_margin(current_income)
        gross_margin_previous = self._calculate_gross_margin(previous_income) if previous_income else None
        
        if gross_margin_current is not None:
            indicators["gross_margin"] = {
                "name": "毛利率",
                "current": gross_margin_current,
                "previous": gross_margin_previous,
                "change": (gross_margin_current - gross_margin_previous) 
                         if gross_margin_previous is not None else None,
                "unit": "%"
            }
        
        # 2. 研发费用率
        rd_expense_current = self._get_value(current_income, "rd_expense")
        revenue_current = self._get_value(current_income, "revenue")
        
        if rd_expense_current is not None and revenue_current:
            rd_expense_ratio = (rd_expense_current / revenue_current) * 100
            
            # 计算上期
            rd_expense_previous = self._get_value(previous_income, "rd_expense")
            revenue_previous = self._get_value(previous_income, "revenue")
            rd_expense_ratio_previous = None
            if rd_expense_previous is not None and revenue_previous:
                rd_expense_ratio_previous = (rd_expense_previous / revenue_previous) * 100
            
            indicators["rd_expense"] = {
                "name": "研发费用",
                "current": rd_expense_current,
                "previous": rd_expense_previous,
                "growth_rate": self._calculate_growth_rate(rd_expense_current, rd_expense_previous),
                "ratio": rd_expense_ratio,
                "ratio_previous": rd_expense_ratio_previous,
                "ratio_change": (rd_expense_ratio - rd_expense_ratio_previous) 
                               if rd_expense_ratio_previous is not None else None,
                "unit": "元",
                "display_format": self._format_large_number(rd_expense_current)
            }
        
        # 3. 销售费用率
        sales_expense_current = self._get_value(current_income, "sales_expense")
        
        if sales_expense_current is not None and revenue_current:
            sales_expense_ratio = (sales_expense_current / revenue_current) * 100
            
            sales_expense_previous = self._get_value(previous_income, "sales_expense")
            revenue_previous = self._get_value(previous_income, "revenue")
            sales_expense_ratio_previous = None
            if sales_expense_previous is not None and revenue_previous:
                sales_expense_ratio_previous = (sales_expense_previous / revenue_previous) * 100
            
            indicators["sales_expense"] = {
                "name": "销售费用",
                "current": sales_expense_current,
                "previous": sales_expense_previous,
                "ratio": sales_expense_ratio,
                "ratio_previous": sales_expense_ratio_previous,
                "ratio_change": (sales_expense_ratio - sales_expense_ratio_previous) 
                               if sales_expense_ratio_previous is not None else None,
                "unit": "元",
                "display_format": self._format_large_number(sales_expense_current)
            }
        
        return indicators
    
    def _extract_specific_indicators(
        self,
        current_data: Dict[str, Any],
        previous_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """提取个性化指标"""
        indicators = {}
        
        current_balance = current_data.get("balance_sheet", {})
        previous_balance = previous_data.get("balance_sheet", {}) if previous_data else {}
        
        # 1. 合同负债（订阅制公司）
        contract_liability_current = self._get_value(current_balance, "contract_liability")
        contract_liability_previous = self._get_value(previous_balance, "contract_liability")
        
        if contract_liability_current is not None:
            indicators["contract_liability"] = {
                "name": "合同负债",
                "current": contract_liability_current,
                "previous": contract_liability_previous,
                "change_rate": self._calculate_growth_rate(
                    contract_liability_current, contract_liability_previous
                ),
                "change_amount": (contract_liability_current - contract_liability_previous) 
                                if contract_liability_previous is not None else None,
                "unit": "元",
                "display_format": self._format_large_number(contract_liability_current)
            }
        
        # 2. 存货（硬件公司）
        inventory_current = self._get_value(current_balance, "inventory")
        inventory_previous = self._get_value(previous_balance, "inventory")
        
        if inventory_current is not None:
            indicators["inventory"] = {
                "name": "存货",
                "current": inventory_current,
                "previous": inventory_previous,
                "change_rate": self._calculate_growth_rate(inventory_current, inventory_previous),
                "change_amount": (inventory_current - inventory_previous) 
                                if inventory_previous is not None else None,
                "unit": "元",
                "display_format": self._format_large_number(inventory_current)
            }
        
        return indicators
    
    def _calculate_gross_margin(self, income_statement: Dict) -> Optional[float]:
        """计算毛利率
        
        毛利率 = (营业收入 - 营业成本) / 营业收入 * 100%
        """
        revenue = self._get_value(income_statement, "revenue")
        cost = self._get_value(income_statement, "cost")
        
        if revenue and cost and revenue != 0:
            gross_profit = revenue - cost
            gross_margin = (gross_profit / revenue) * 100
            return round(gross_margin, 2)
        
        return None
    
    def _calculate_growth_rate(
        self,
        current: Optional[float],
        previous: Optional[float]
    ) -> Optional[float]:
        """计算增长率
        
        增长率 = (本期 - 上期) / 上期 * 100%
        """
        if current is None or previous is None:
            return None
        
        if previous == 0:
            return None  # 避免除零
        
        growth_rate = ((current - previous) / abs(previous)) * 100
        return round(growth_rate, 2)
    
    def _get_value(self, data: Dict, key: str) -> Optional[float]:
        """从字典中获取值
        
        Args:
            data: 数据字典
            key: 键名
            
        Returns:
            找到的值，如果不存在则返回None
        """
        if not data or key not in data:
            return None
        
        value = data[key]
        if value is None:
            return None
        
        # 尝试转换为float
        try:
            if isinstance(value, (int, float, Decimal)):
                return float(value)
            elif isinstance(value, str):
                # 移除可能的逗号和空格
                cleaned = value.replace(",", "").replace(" ", "")
                return float(cleaned)
        except (ValueError, InvalidOperation):
            logger.warning(f"无法转换值为数字: {key}={value}")
            return None
        
        return None
    
    def _format_large_number(self, number: float) -> str:
        """格式化大数字显示
        
        Args:
            number: 数字
            
        Returns:
            格式化后的字符串，如 "1.23亿元"
        """
        if number is None:
            return "N/A"
        
        abs_number = abs(number)
        sign = "-" if number < 0 else ""
        
        if abs_number >= 100_000_000:  # 亿
            return f"{sign}{abs_number / 100_000_000:.2f}亿"
        elif abs_number >= 10_000:  # 万
            return f"{sign}{abs_number / 10_000:.2f}万"
        else:
            return f"{sign}{abs_number:.2f}"
    
    def format_indicators_for_display(self, indicators: Dict[str, Any]) -> str:
        """将指标格式化为可读文本
        
        Args:
            indicators: 指标字典
            
        Returns:
            格式化后的文本
        """
        lines = []
        
        # 核心指标
        if "core" in indicators:
            lines.append("### 核心指标")
            for key, value in indicators["core"].items():
                name = value.get("name", key)
                current = value.get("display_format", value.get("current"))
                growth = value.get("growth_rate")
                
                if growth is not None:
                    lines.append(f"- {name}: {current}元 (同比增长: {growth:+.2f}%)")
                else:
                    lines.append(f"- {name}: {current}元")
        
        # 辅助指标
        if "auxiliary" in indicators:
            lines.append("\n### 辅助指标")
            for key, value in indicators["auxiliary"].items():
                name = value.get("name", key)
                
                if "ratio" in value:
                    ratio = value.get("ratio")
                    ratio_change = value.get("ratio_change")
                    if ratio_change is not None:
                        lines.append(f"- {name}: {ratio:.2f}% (变动: {ratio_change:+.2f}pp)")
                    else:
                        lines.append(f"- {name}: {ratio:.2f}%")
                else:
                    current = value.get("display_format", value.get("current"))
                    growth = value.get("growth_rate")
                    if growth is not None:
                        lines.append(f"- {name}: {current}元 (增长: {growth:+.2f}%)")
                    else:
                        lines.append(f"- {name}: {current}元")
        
        # 个性化指标
        if "specific" in indicators and indicators["specific"]:
            lines.append("\n### 个性化指标")
            for key, value in indicators["specific"].items():
                name = value.get("name", key)
                current = value.get("display_format", value.get("current"))
                change = value.get("change_rate")
                
                if change is not None:
                    lines.append(f"- {name}: {current}元 (变化: {change:+.2f}%)")
                else:
                    lines.append(f"- {name}: {current}元")
        
        return "\n".join(lines)
