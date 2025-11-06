"""行业配置模块

根据不同行业定义核心指标、辅助指标和个性化指标
支持行业扩展
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class IndicatorPriority(str, Enum):
    """指标优先级"""
    CORE = "core"  # 核心指标
    AUXILIARY = "auxiliary"  # 辅助指标
    SPECIFIC = "specific"  # 个性化指标


@dataclass
class IndicatorConfig:
    """指标配置"""
    name: str  # 指标名称
    display_name: str  # 显示名称
    priority: IndicatorPriority  # 优先级
    description: str  # 描述
    calculation_method: Optional[str] = None  # 计算方法
    unit: str = ""  # 单位
    db_fields: List[str] = field(default_factory=list)  # 数据库字段名


@dataclass
class IndustryCharacteristics:
    """行业特征"""
    name: str  # 特征名称
    description: str  # 描述


@dataclass
class IndustryConfig:
    """行业配置"""
    code: str  # 行业代码
    name: str  # 行业名称
    description: str  # 行业描述
    characteristics: List[IndustryCharacteristics]  # 行业特征
    indicators: List[IndicatorConfig]  # 指标配置列表
    
    def get_indicators_by_priority(self, priority: IndicatorPriority) -> List[IndicatorConfig]:
        """按优先级获取指标"""
        return [ind for ind in self.indicators if ind.priority == priority]
    
    def get_core_indicators(self) -> List[IndicatorConfig]:
        """获取核心指标"""
        return self.get_indicators_by_priority(IndicatorPriority.CORE)
    
    def get_auxiliary_indicators(self) -> List[IndicatorConfig]:
        """获取辅助指标"""
        return self.get_indicators_by_priority(IndicatorPriority.AUXILIARY)
    
    def get_specific_indicators(self) -> List[IndicatorConfig]:
        """获取个性化指标"""
        return self.get_indicators_by_priority(IndicatorPriority.SPECIFIC)


# ==================== 计算机行业配置 ====================

COMPUTER_INDUSTRY_CONFIG = IndustryConfig(
    code="computer",
    name="计算机",
    description="TMT高风险偏好板块，以成长性和高估值为特征",
    characteristics=[
        IndustryCharacteristics(
            name="成长性",
            description="属于TMT高风偏板块，成长性和想象空间显著影响估值"
        ),
        IndustryCharacteristics(
            name="高估值",
            description="估值倍数相比传统行业偏高，甚至采用终局估值法"
        ),
        IndustryCharacteristics(
            name="业绩不可预测",
            description="业绩可预测性差，主观调节能力强，不适用传统行业的细拆报表预测方法"
        )
    ],
    indicators=[
        # ==================== 核心指标 ====================
        IndicatorConfig(
            name="revenue_growth",
            display_name="营业收入增速",
            priority=IndicatorPriority.CORE,
            description="最直接影响股价的核心指标，反映公司成长性",
            calculation_method="(本期营业收入 - 上期营业收入) / 上期营业收入 * 100%",
            unit="%",
            db_fields=["b001101000", "b001101000_prev"]  # 营业收入（本期、上期）
        ),
        IndicatorConfig(
            name="segment_revenue_growth",
            display_name="细分板块收入增速",
            priority=IndicatorPriority.CORE,
            description="某些关键业务板块的增速可能是股价决定因素",
            calculation_method="分板块计算增速",
            unit="%",
            db_fields=[]  # 需要从补充数据中获取
        ),
        IndicatorConfig(
            name="net_profit_growth",
            display_name="净利润增速",
            priority=IndicatorPriority.CORE,
            description="次要核心指标，重要性弱于收入增速",
            calculation_method="(本期净利润 - 上期净利润) / 上期净利润 * 100%",
            unit="%",
            db_fields=["b002000000", "b002000000_prev"]  # 净利润
        ),
        
        # ==================== 辅助指标 ====================
        IndicatorConfig(
            name="gross_margin",
            display_name="毛利率",
            priority=IndicatorPriority.AUXILIARY,
            description="反映增速的质量和健康程度，与收入增速结合判断",
            calculation_method="(营业收入 - 营业成本) / 营业收入 * 100%",
            unit="%",
            db_fields=["b001101000", "b001201000"]  # 营业收入、营业成本
        ),
        IndicatorConfig(
            name="rd_expense_ratio",
            display_name="研发费用率",
            priority=IndicatorPriority.AUXILIARY,
            description="增速/战略的先导性指标，造假程度低",
            calculation_method="研发费用 / 营业收入 * 100%",
            unit="%",
            db_fields=["b001216000", "b001101000"]  # 研发费用、营业收入
        ),
        IndicatorConfig(
            name="sales_expense_ratio",
            display_name="销售费用率",
            priority=IndicatorPriority.AUXILIARY,
            description="反映商务费用或投流费用，是收入增速的重要指标",
            calculation_method="销售费用 / 营业收入 * 100%",
            unit="%",
            db_fields=["b001209000", "b001101000"]  # 销售费用、营业收入
        ),
        
        # ==================== 个性化指标 ====================
        IndicatorConfig(
            name="contract_liability_change",
            display_name="合同负债变化",
            priority=IndicatorPriority.SPECIFIC,
            description="对云计算等订阅制公司，反映未确认收入，有很强的增长先导性",
            calculation_method="(本期合同负债 - 上期合同负债) / 上期合同负债 * 100%",
            unit="%",
            db_fields=["a002128000", "a002128000_prev"]  # 合同负债
        ),
        IndicatorConfig(
            name="inventory_change",
            display_name="存货季度环比变化",
            priority=IndicatorPriority.SPECIFIC,
            description="对算力/服务器公司，反映未确认收入的硬件产品，是收入先导性指标",
            calculation_method="本期存货 - 上期存货",
            unit="元",
            db_fields=["a001123000", "a001123000_prev"]  # 存货
        ),
    ]
)


# ==================== 行业配置管理器 ====================

class IndustryConfigManager:
    """行业配置管理器"""
    
    def __init__(self):
        self._configs: Dict[str, IndustryConfig] = {
            "computer": COMPUTER_INDUSTRY_CONFIG,
        }
    
    def get_config(self, industry: str) -> IndustryConfig:
        """获取行业配置
        
        Args:
            industry: 行业代码或名称
            
        Returns:
            行业配置
            
        Raises:
            ValueError: 行业不存在
        """
        # 支持通过代码或名称查询
        if industry in self._configs:
            return self._configs[industry]
        
        # 尝试通过名称查询
        for config in self._configs.values():
            if config.name == industry:
                return config
        
        raise ValueError(f"不支持的行业: {industry}，当前支持: {list(self._configs.keys())}")
    
    def register_config(self, config: IndustryConfig):
        """注册新的行业配置"""
        self._configs[config.code] = config
    
    def list_industries(self) -> List[str]:
        """列出所有支持的行业"""
        return list(self._configs.keys())


# 全局配置管理器实例
industry_config_manager = IndustryConfigManager()

