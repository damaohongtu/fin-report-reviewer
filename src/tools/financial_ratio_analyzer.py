"""财务比率分析工具

计算13种核心财务比率，输入为利润表、资产负债表、现金流量表。
支持季报和年报的计算，季报数据将进行年化处理。
无法计算的指标值返回 None 并记录原因。
"""
import math
from typing import Dict, Any, Optional
from decimal import Decimal, InvalidOperation
from datetime import datetime

from langchain_core.tools import tool
from loguru import logger


# ==================== 工具函数 ====================

def _safe_float(value: Any) -> Optional[float]:
    """安全转换为 float，转换失败或 NaN 均返回 None"""
    if value is None:
        return None
    try:
        if isinstance(value, (int, float, Decimal)):
            f = float(value)
            return None if math.isnan(f) else f
        if isinstance(value, str):
            cleaned = value.replace(",", "").replace(" ", "")
            if not cleaned:
                return None
            f = float(cleaned)
            return None if math.isnan(f) else f
    except (ValueError, InvalidOperation):
        return None
    return None


def _safe_divide(
    numerator: Optional[float],
    denominator: Optional[float],
    scale: float = 1.0,
    decimal_places: int = 4,
) -> Optional[float]:
    """安全除法，分母为 0、任意操作数为 None 或 NaN 时返回 None"""
    if numerator is None or denominator is None:
        return None
    if math.isnan(numerator) or math.isnan(denominator) or denominator == 0:
        return None
    return round((numerator / denominator) * scale, decimal_places)


def _avg(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """计算两期均值；只有一期数据时直接使用该期数据"""
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return (a + b) / 2


def _annualization_factor(report_period: str) -> float:
    """
    根据报告期日期计算年化系数：
      3月底(Q1)  → 4.0
      6月底(Q2)  → 2.0
      9月底(Q3)  → 4/3 ≈ 1.333
      12月底(年) → 1.0
    """
    try:
        month = datetime.strptime(report_period, "%Y-%m-%d").month
        return {3: 4.0, 6: 2.0, 9: 4.0 / 3.0, 12: 1.0}.get(month, 1.0)
    except ValueError:
        return 1.0


def _is_quarterly(report_period: str) -> bool:
    """判断是否为非年报期（季报/半年报）"""
    try:
        return datetime.strptime(report_period, "%Y-%m-%d").month != 12
    except ValueError:
        return False


def _g(data: Dict[str, Any], key: str) -> Optional[float]:
    """从财务数据字典中安全取值"""
    return _safe_float(data.get(key))


# ==================== 比率计算核心逻辑 ====================

class _RatioCalculator:
    """财务比率计算器（内部使用）"""

    def __init__(
        self,
        income: Dict[str, Any],
        balance: Dict[str, Any],
        cash_flow: Dict[str, Any],
        prev_balance: Optional[Dict[str, Any]],
        report_period: str,
    ):
        self.income = income
        self.balance = balance
        self.cash_flow = cash_flow
        self.prev_balance = prev_balance or {}
        self.report_period = report_period
        self.ann = _annualization_factor(report_period)
        self.quarterly = _is_quarterly(report_period)

    # ---------- 快捷取值 ----------

    def _i(self, key: str) -> Optional[float]:
        return _g(self.income, key)

    def _b(self, key: str) -> Optional[float]:
        return _g(self.balance, key)

    def _pb(self, key: str) -> Optional[float]:
        return _g(self.prev_balance, key)

    def _cf(self, key: str) -> Optional[float]:
        return _g(self.cash_flow, key)

    def _b_avg(self, key: str) -> Optional[float]:
        """资产负债表科目的期初期末均值"""
        return _avg(self._b(key), self._pb(key))

    # ---------- 核心利润（多处复用） ----------

    def _core_profit(self) -> Optional[float]:
        """
        核心利润 = 营业收入 - 营业成本 - 税金及附加
                  - 销售费用 - 管理费用 - 研发费用
        """
        revenue = self._i("revenue")
        cost = self._i("cost")
        if revenue is None or cost is None:
            return None

        deductions = [
            self._i("business_tax") or 0.0,
            self._i("sales_expense") or 0.0,
            self._i("admin_expense") or 0.0,
            self._i("rd_expense") or 0.0,
        ]
        return revenue - cost - sum(deductions)

    # ---------- 13 种比率 ----------

    def gross_margin(self) -> Dict[str, Any]:
        """1. 毛利率 = (营业收入 - 营业成本) / 营业收入"""
        revenue = self._i("revenue")
        cost = self._i("cost")
        value = _safe_divide(
            (revenue - cost) if revenue is not None and cost is not None else None,
            revenue,
            scale=100,
            decimal_places=2,
        )
        return {
            "name": "毛利率",
            "formula": "(营业收入 - 营业成本) / 营业收入",
            "value": value,
            "unit": "%",
            "available": value is not None,
        }

    def core_profit_margin(self) -> Dict[str, Any]:
        """2. 核心利润率 = 核心利润 / 营业收入"""
        revenue = self._i("revenue")
        cp = self._core_profit()
        value = _safe_divide(cp, revenue, scale=100, decimal_places=2)
        return {
            "name": "核心利润率",
            "formula": "(营业收入-营业成本-税金及附加-销售费用-管理费用-研发费用) / 营业收入",
            "value": value,
            "core_profit": cp,
            "unit": "%",
            "available": value is not None,
        }

    def return_on_total_assets(self) -> Dict[str, Any]:
        """
        3. 总资产报酬率 = EBIT / 平均资产总额
           EBIT = 利润总额 + 利息费用
           利息费用优先取 interest_expense（财务费用利息部分），
           若缺失则退而使用 finance_expense（财务费用合计，含利息收入负值，为近似值）。
           季报时对 EBIT 进行年化处理。
        """
        total_profit = self._i("total_profit")
        interest_expense = self._i("interest_expense") or self._i("finance_expense")
        avg_assets = self._b_avg("total_assets")

        ebit: Optional[float] = None
        if total_profit is not None:
            ebit = total_profit + (interest_expense or 0.0)

        if ebit is not None and self.quarterly:
            ebit = ebit * self.ann

        value = _safe_divide(ebit, avg_assets, scale=100, decimal_places=2)
        return {
            "name": "总资产报酬率",
            "formula": "EBIT(年化) / 平均资产总额",
            "value": value,
            "ebit": ebit,
            "avg_total_assets": avg_assets,
            "annualized": self.quarterly,
            "unit": "%",
            "available": value is not None,
        }

    def return_on_equity(self) -> Dict[str, Any]:
        """
        4. 净资产收益率(ROE) = 净利润(年化) / 平均净资产
        """
        net_profit = self._i("net_profit")
        avg_equity = self._b_avg("total_equity")

        net_profit_ann: Optional[float] = None
        if net_profit is not None:
            net_profit_ann = net_profit * self.ann if self.quarterly else net_profit

        value = _safe_divide(net_profit_ann, avg_equity, scale=100, decimal_places=2)
        return {
            "name": "净资产收益率(ROE)",
            "formula": "净利润(年化) / 平均净资产",
            "value": value,
            "net_profit_annualized": net_profit_ann,
            "avg_equity": avg_equity,
            "annualized": self.quarterly,
            "unit": "%",
            "available": value is not None,
        }

    def inventory_turnover(self) -> Dict[str, Any]:
        """
        5. 存货周转率 = 营业成本(年化) / 平均存货
        """
        cost = self._i("cost")
        avg_inventory = self._b_avg("inventory")

        cost_ann: Optional[float] = None
        if cost is not None:
            cost_ann = cost * self.ann if self.quarterly else cost

        value = _safe_divide(cost_ann, avg_inventory, decimal_places=4)
        return {
            "name": "存货周转率",
            "formula": "营业成本(年化) / 平均存货",
            "value": value,
            "cost_annualized": cost_ann,
            "avg_inventory": avg_inventory,
            "annualized": self.quarterly,
            "unit": "次",
            "available": value is not None,
        }

    def fixed_asset_turnover(self) -> Dict[str, Any]:
        """
        6. 固定资产周转率 = 营业收入(年化) / 平均固定资产净额
           注：需要资产负债表中的 fixed_assets 字段（a001212000）
        """
        revenue = self._i("revenue")
        avg_fixed = self._b_avg("fixed_assets")

        revenue_ann: Optional[float] = None
        if revenue is not None:
            revenue_ann = revenue * self.ann if self.quarterly else revenue

        value = _safe_divide(revenue_ann, avg_fixed, decimal_places=4)
        return {
            "name": "固定资产周转率",
            "formula": "营业收入(年化) / 平均固定资产净额",
            "value": value,
            "revenue_annualized": revenue_ann,
            "avg_fixed_assets": avg_fixed,
            "annualized": self.quarterly,
            "unit": "次",
            "available": value is not None,
            "required_fields": ["fixed_assets (资产负债表固定资产净额 a001212000)"],
        }

    def operating_asset_turnover(self) -> Dict[str, Any]:
        """
        7. 经营资产周转率 = 营业收入(年化) / 平均经营资产
           经营资产 = 资产总额 - 投资资产
           投资资产 = 交易性金融资产 + 可供出售金融资产/其他权益工具投资
                    + 持有至到期投资 + 长期股权投资 + 债权投资
                    + 其他非流动金融资产
        """
        revenue = self._i("revenue")
        revenue_ann: Optional[float] = None
        if revenue is not None:
            revenue_ann = revenue * self.ann if self.quarterly else revenue

        def _investment_assets(d: Dict[str, Any]) -> Optional[float]:
            total_assets = _g(d, "total_assets")
            if total_assets is None:
                return None
            investment_keys = [
                "trading_financial_assets",       # a001107000 交易性金融资产
                "available_for_sale_assets",      # a001202000 可供出售金融资产
                "held_to_maturity_investments",   # a001203000 持有至到期投资
                "long_term_equity_investment",    # a001205000 长期股权投资
                "debt_investments",               # a001226000 债权投资
                "other_equity_instruments_invest",# a001228000 其他权益工具投资
                "other_noncurrent_financial_assets",  # a001229000 其他非流动金融资产
            ]
            # None（缺失字段）按 0 处理，NaN 已由 _g/_safe_float 转为 None
            invest_total = sum(v for k in investment_keys if (v := _g(d, k)) is not None)
            return total_assets - invest_total

        op_assets_curr = _investment_assets(self.balance)
        op_assets_prev = _investment_assets(self.prev_balance) if self.prev_balance else None
        avg_op_assets = _avg(op_assets_curr, op_assets_prev)

        value = _safe_divide(revenue_ann, avg_op_assets, decimal_places=4)
        return {
            "name": "经营资产周转率",
            "formula": "营业收入(年化) / 平均经营资产 (经营资产=资产总额-投资资产)",
            "value": value,
            "revenue_annualized": revenue_ann,
            "avg_operating_assets": avg_op_assets,
            "operating_assets_current": op_assets_curr,
            "annualized": self.quarterly,
            "unit": "次",
            "available": value is not None,
            "required_fields": [
                "trading_financial_assets, available_for_sale_assets, "
                "held_to_maturity_investments, long_term_equity_investment 等投资类资产字段"
            ],
        }

    def current_ratio(self) -> Dict[str, Any]:
        """8. 流动比率 = 流动资产 / 流动负债"""
        current_assets = self._b("current_assets")
        current_liabilities = self._b("current_liabilities")
        value = _safe_divide(current_assets, current_liabilities, decimal_places=4)
        return {
            "name": "流动比率",
            "formula": "流动资产 / 流动负债",
            "value": value,
            "current_assets": current_assets,
            "current_liabilities": current_liabilities,
            "unit": "倍",
            "available": value is not None,
        }

    def debt_to_asset_ratio(self) -> Dict[str, Any]:
        """9. 资产负债率 = 负债合计 / 资产总计"""
        total_liabilities = self._b("total_liabilities")
        total_assets = self._b("total_assets")
        value = _safe_divide(total_liabilities, total_assets, scale=100, decimal_places=2)
        return {
            "name": "资产负债率",
            "formula": "负债合计 / 资产总计",
            "value": value,
            "total_liabilities": total_liabilities,
            "total_assets": total_assets,
            "unit": "%",
            "available": value is not None,
        }

    def financial_liability_ratio(self) -> Dict[str, Any]:
        """
        10. 资产金融性负债率（有息负债率）= 金融性负债 / 资产总额
            金融性负债 = 短期借款 + 交易性金融负债 + 一年内到期的非流动负债
                       + 长期借款 + 应付债券 + 租赁负债
        """
        total_assets = self._b("total_assets")
        financial_liability_keys = [
            "short_term_borrowing",              # a002101000 短期借款
            "trading_financial_liabilities",     # a002105000 交易性金融负债
            "current_noncurrent_liabilities",    # a002125000 一年内到期的非流动负债
            "long_term_borrowing",               # a002201000 长期借款
            "bonds_payable",                     # a002203000 应付债券
            "lease_liabilities",                 # a002211000 租赁负债
        ]
        available_values = {k: self._b(k) for k in financial_liability_keys}
        # 只累加有效值（None 和 NaN 视为缺失，按 0 处理但需至少一个有效值）
        valid_values = [v for v in available_values.values() if v is not None]
        has_any = bool(valid_values)

        fin_liabilities: Optional[float] = None
        if has_any:
            fin_liabilities = sum(valid_values)

        value = _safe_divide(fin_liabilities, total_assets, scale=100, decimal_places=2)
        return {
            "name": "资产金融性负债率",
            "formula": "金融性负债(短期借款+应付债券+长期借款+租赁负债+...) / 资产总额",
            "value": value,
            "financial_liabilities": fin_liabilities,
            "total_assets": total_assets,
            "components": available_values,
            "unit": "%",
            "available": value is not None,
            "required_fields": financial_liability_keys,
        }

    def operating_liability_ratio(self) -> Dict[str, Any]:
        """
        11. 资产经营性负债率 = 经营性负债 / 资产总额
            经营性负债 = 负债合计 - 金融性负债
        """
        total_assets = self._b("total_assets")
        total_liabilities = self._b("total_liabilities")

        # 复用金融性负债逻辑
        fin_ratio_result = self.financial_liability_ratio()
        fin_liabilities = fin_ratio_result.get("financial_liabilities")

        op_liabilities: Optional[float] = None
        if total_liabilities is not None and fin_liabilities is not None:
            op_liabilities = total_liabilities - fin_liabilities
        elif total_liabilities is not None and not fin_ratio_result["available"]:
            # 金融性负债字段全部缺失时，无法拆分
            op_liabilities = None

        value = _safe_divide(op_liabilities, total_assets, scale=100, decimal_places=2)
        return {
            "name": "资产经营性负债率",
            "formula": "经营性负债(负债合计-金融性负债) / 资产总额",
            "value": value,
            "operating_liabilities": op_liabilities,
            "total_assets": total_assets,
            "unit": "%",
            "available": value is not None,
            "required_fields": fin_ratio_result.get("required_fields", []),
        }

    def core_profit_cash_ratio(self) -> Dict[str, Any]:
        """
        12. 核心利润获现率 = 经营活动现金流量净额 / 核心利润
        """
        op_cash_flow = self._cf("net_operating_cash_flow")
        cp = self._core_profit()
        value = _safe_divide(op_cash_flow, cp, decimal_places=4)
        return {
            "name": "核心利润获现率",
            "formula": "经营活动现金流量净额 / 核心利润",
            "value": value,
            "net_operating_cash_flow": op_cash_flow,
            "core_profit": cp,
            "unit": "倍",
            "available": value is not None,
        }

    def dupont_analysis(self) -> Dict[str, Any]:
        """
        13. 杜邦分析法
            ROE = 净利润率 × 总资产周转率 × 权益乘数
            - 净利润率        = 净利润 / 营业收入
            - 总资产周转率    = 营业收入(年化) / 平均总资产
            - 权益乘数        = 平均总资产 / 平均净资产
        """
        net_profit = self._i("net_profit")
        revenue = self._i("revenue")
        avg_total_assets = self._b_avg("total_assets")
        avg_equity = self._b_avg("total_equity")

        # 季报：净利润和营业收入均需年化（年化后两者相除，年化系数抵消，净利润率无需单独年化）
        revenue_ann: Optional[float] = None
        if revenue is not None:
            revenue_ann = revenue * self.ann if self.quarterly else revenue
        net_profit_ann: Optional[float] = None
        if net_profit is not None:
            net_profit_ann = net_profit * self.ann if self.quarterly else net_profit

        net_profit_margin = _safe_divide(net_profit_ann, revenue_ann, scale=100, decimal_places=2)
        asset_turnover = _safe_divide(revenue_ann, avg_total_assets, decimal_places=4)
        equity_multiplier = _safe_divide(avg_total_assets, avg_equity, decimal_places=4)

        # ROE(%) = 净利润率(%) × 总资产周转率(倍) × 权益乘数(倍)
        # net_profit_margin 已是百分比值，相乘后结果仍为百分比
        roe_dupont: Optional[float] = None
        if all(v is not None for v in [net_profit_margin, asset_turnover, equity_multiplier]):
            roe_dupont = round(net_profit_margin * asset_turnover * equity_multiplier, 2)

        return {
            "name": "杜邦分析法",
            "formula": "ROE = 净利润率 × 总资产周转率 × 权益乘数",
            "roe": roe_dupont,
            "components": {
                "net_profit_margin": {
                    "name": "净利润率",
                    "value": net_profit_margin,
                    "formula": "净利润(年化) / 营业收入(年化)",
                    "unit": "%",
                },
                "asset_turnover": {
                    "name": "总资产周转率",
                    "value": asset_turnover,
                    "formula": "营业收入(年化) / 平均总资产",
                    "unit": "次",
                },
                "equity_multiplier": {
                    "name": "权益乘数",
                    "value": equity_multiplier,
                    "formula": "平均总资产 / 平均净资产",
                    "unit": "倍",
                },
            },
            "annualized": self.quarterly,
            "unit": "%",
            "available": roe_dupont is not None,
        }

    def compute_all(self) -> Dict[str, Any]:
        """计算全部13种比率，汇总返回"""
        results = {
            "gross_margin": self.gross_margin(),
            "core_profit_margin": self.core_profit_margin(),
            "return_on_total_assets": self.return_on_total_assets(),
            "return_on_equity": self.return_on_equity(),
            "inventory_turnover": self.inventory_turnover(),
            "fixed_asset_turnover": self.fixed_asset_turnover(),
            "operating_asset_turnover": self.operating_asset_turnover(),
            "current_ratio": self.current_ratio(),
            "debt_to_asset_ratio": self.debt_to_asset_ratio(),
            "financial_liability_ratio": self.financial_liability_ratio(),
            "operating_liability_ratio": self.operating_liability_ratio(),
            "core_profit_cash_ratio": self.core_profit_cash_ratio(),
            "dupont_analysis": self.dupont_analysis(),
        }

        available_count = sum(1 for v in results.values() if v.get("available"))
        unavailable = [v["name"] for v in results.values() if not v.get("available")]

        if unavailable:
            logger.warning(f"以下比率因数据缺失无法计算: {unavailable}")

        logger.info(f"财务比率计算完成: {available_count}/13 项可用")
        return results


# ==================== LangChain Tool ====================

@tool
def calculate_financial_ratios_tool(
    income_statement: Dict[str, Any],
    balance_sheet: Dict[str, Any],
    cash_flow: Dict[str, Any],
    previous_balance_sheet: Optional[Dict[str, Any]] = None,
    report_period: str = "",
) -> Dict[str, Any]:
    """计算13种核心财务比率

    支持季报和年报（季报数据自动年化）。所有比率一次性返回，
    数据缺失时对应比率的 value 为 None，available 为 False。

    输入字段说明（使用财报数据服务的别名字段名）：

    income_statement（利润表）：
      revenue, cost, business_tax, sales_expense, admin_expense,
      rd_expense, finance_expense, interest_expense（可选，更精确的利息费用）,
      total_profit, net_profit

    balance_sheet（资产负债表，当期末）：
      current_assets, non_current_assets, total_assets,
      current_liabilities, non_current_liabilities, total_liabilities,
      total_equity, inventory,
      fixed_assets（固定资产净额，用于比率6）,
      trading_financial_assets, available_for_sale_assets,
      held_to_maturity_investments, long_term_equity_investment,
      debt_investments, other_equity_instruments_invest,
      other_noncurrent_financial_assets（用于比率7经营资产），
      short_term_borrowing, trading_financial_liabilities,
      current_noncurrent_liabilities, long_term_borrowing,
      bonds_payable, lease_liabilities（用于比率10/11金融性负债）

    cash_flow（现金流量表）：
      net_operating_cash_flow

    previous_balance_sheet（上期末资产负债表，与当期同字段）：
      用于计算期初期末均值，缺失时直接使用期末数据

    report_period：报告期日期，格式 "YYYY-MM-DD"，如 "2024-03-31"

    Args:
        income_statement: 利润表数据字典
        balance_sheet: 当期末资产负债表数据字典
        cash_flow: 现金流量表数据字典
        previous_balance_sheet: 上期末资产负债表（可选，用于均值计算）
        report_period: 报告期日期字符串

    Returns:
        包含13种财务比率的字典，每项结构：
        {
            "name": 比率名称,
            "formula": 计算公式说明,
            "value": 计算结果（float 或 None）,
            "unit": 单位,
            "available": 是否可计算 (bool),
            ...其他中间数据
        }
    """
    logger.info(f"Tool调用: 计算财务比率 - 报告期:{report_period}")

    calculator = _RatioCalculator(
        income=income_statement,
        balance=balance_sheet,
        cash_flow=cash_flow,
        prev_balance=previous_balance_sheet,
        report_period=report_period,
    )
    return calculator.compute_all()


# ==================== 主程序入口 ====================

def _fmt_value(value: Optional[float], unit: str) -> str:
    """格式化比率值用于打印"""
    if value is None or value != value:  # None 或 NaN
        return "N/A"
    if unit == "%":
        return f"{value:.2f}%"
    if unit == "倍":
        return f"{value:.4f}x"
    if unit == "次":
        return f"{value:.4f}次/年"
    return str(value)


def _fmt_amount(value: Optional[float]) -> str:
    """格式化金额（亿元）"""
    if value is None or value != value:  # None 或 NaN
        return "N/A"
    sign = "-" if value < 0 else ""
    abs_v = abs(value)
    if abs_v >= 1e8:
        return f"{sign}{abs_v / 1e8:.2f}亿"
    if abs_v >= 1e4:
        return f"{sign}{abs_v / 1e4:.2f}万"
    return f"{sign}{abs_v:.2f}"


def _print_ratios(ratios: Dict[str, Any], stock_code: str, report_period: str) -> None:
    """格式化打印13种比率结果"""
    sep = "=" * 62

    print(f"\n{sep}")
    print(f"  财务比率分析报告  {stock_code}  {report_period}")
    print(sep)

    sections = [
        ("盈利能力", ["gross_margin", "core_profit_margin",
                    "return_on_total_assets", "return_on_equity"]),
        ("营运效率", ["inventory_turnover", "fixed_asset_turnover",
                    "operating_asset_turnover"]),
        ("偿债能力", ["current_ratio", "debt_to_asset_ratio",
                    "financial_liability_ratio", "operating_liability_ratio"]),
        ("现金质量", ["core_profit_cash_ratio"]),
        ("杜邦分析", ["dupont_analysis"]),
    ]

    available_total = sum(1 for v in ratios.values() if v.get("available"))

    for section_name, keys in sections:
        print(f"\n【{section_name}】")
        for key in keys:
            r = ratios.get(key, {})
            name = r.get("name", key)
            unit = r.get("unit", "")
            ann_flag = "  (已年化)" if r.get("annualized") else ""

            if key == "dupont_analysis":
                # 杜邦单独展示分解
                roe_val = r.get("roe")
                status = "✅" if r.get("available") else "❌"
                print(f"  {status} {name}: {_fmt_value(roe_val, '%')}{ann_flag}")
                for comp_key, comp in r.get("components", {}).items():
                    comp_val = comp.get("value")
                    comp_unit = comp.get("unit", "")
                    comp_name = comp.get("name", comp_key)
                    print(f"       ├ {comp_name}: {_fmt_value(comp_val, comp_unit)}")
            else:
                value = r.get("value")
                status = "✅" if r.get("available") else "❌"
                print(f"  {status} {name}: {_fmt_value(value, unit)}{ann_flag}")

                # 补充关键中间值
                if key == "return_on_total_assets":
                    print(f"       ├ EBIT: {_fmt_amount(r.get('ebit'))}"
                          f"  | 平均总资产: {_fmt_amount(r.get('avg_total_assets'))}")
                elif key == "return_on_equity":
                    print(f"       ├ 净利润(年化): {_fmt_amount(r.get('net_profit_annualized'))}"
                          f"  | 平均净资产: {_fmt_amount(r.get('avg_equity'))}")
                elif key == "core_profit_cash_ratio":
                    print(f"       ├ 经营现金流: {_fmt_amount(r.get('net_operating_cash_flow'))}"
                          f"  | 核心利润: {_fmt_amount(r.get('core_profit'))}")
                elif key == "financial_liability_ratio":
                    _FIN_LIB_LABELS = {
                        "short_term_borrowing":           "短期借款",
                        "trading_financial_liabilities":  "交易性金融负债",
                        "current_noncurrent_liabilities": "一年内到期非流动负债",
                        "long_term_borrowing":            "长期借款",
                        "bonds_payable":                  "应付债券",
                        "lease_liabilities":              "租赁负债",
                    }
                    comps = r.get("components", {})
                    # 只显示有效值（过滤 None；NaN 已由 _safe_float 转为 None）
                    shown = {k: v for k, v in comps.items() if v is not None}
                    if shown:
                        parts = "  ".join(
                            f"{_FIN_LIB_LABELS.get(k, k)}: {_fmt_amount(v)}"
                            for k, v in shown.items()
                        )
                        print(f"       ├ {parts}")

    print(f"\n{sep}")
    print(f"  计算完成: {available_total}/13 项可用")
    print(sep)


def main() -> None:
    """
    从命令行查询指定公司财务数据并计算13种比率。

    用法：
        python -m src.tools.financial_ratio_analyzer --stock 600519 --period 2024-12-31
        python -m src.tools.financial_ratio_analyzer --stock 600519 --period 2024-03-31 --type A
    """
    import argparse
    import sys

    # 延迟导入，避免影响工具模块的正常加载
    from src.clients.financial_data_http_client import FinancialDataHttpClient

    parser = argparse.ArgumentParser(description="财务比率分析 - 查询并计算13种核心财务比率")
    parser.add_argument("--stock",  required=True, help="股票代码，如 600519")
    parser.add_argument("--period", required=True, help="报告期，如 2024-12-31")
    parser.add_argument("--type",   default="A",   help="报表类型：A=合并(默认)，B=母公司")
    args = parser.parse_args()

    stock_code   = args.stock
    report_period = args.period
    report_type  = args.type

    print(f"\n正在连接财报数据服务...")
    try:
        client = FinancialDataHttpClient()
    except ConnectionError as e:
        print(f"❌ 无法连接财报数据服务: {e}")
        sys.exit(1)

    print(f"正在获取 {stock_code} {report_period} 财务数据...")
    complete = client.get_complete_financial_data(
        stock_code, report_period, report_type, include_previous=True
    )

    income   = complete.get("income_statement") or {}
    balance  = complete.get("balance_sheet")    or {}
    cashflow = complete.get("cash_flow")        or {}
    prev_data    = complete.get("previous_data") or {}
    prev_balance = prev_data.get("balance_sheet") or {}
    prev_period  = complete.get("previous_period", "")

    if not income and not balance and not cashflow:
        print(f"❌ 未找到 {stock_code} {report_period} 的财务数据，请确认股票代码和报告期")
        sys.exit(1)

    company_name = (income or balance).get("short_name", stock_code)
    print(f"✅ 数据获取成功: {company_name}  上期: {prev_period or '无'}")

    # 计算比率
    calculator = _RatioCalculator(
        income=income,
        balance=balance,
        cash_flow=cashflow,
        prev_balance=prev_balance if prev_balance else None,
        report_period=report_period,
    )
    ratios = calculator.compute_all()

    # 输出结果
    _print_ratios(ratios, f"{company_name}({stock_code})", report_period)


if __name__ == "__main__":
    main()

