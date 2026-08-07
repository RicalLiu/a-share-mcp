"""风控规则，对应 config.yaml 的 risk 段：

- max_single_stock_ratio: 单票市值不得超过总资产比例
- max_daily_loss_ratio: 当日已实现亏损达总资产比例后禁止买入
- require_confirm_ratio: 单笔金额达总资产比例时标记「需重点确认」
- forbid_all_sell: 禁止一键清仓（需 force 二次确认）
"""
from __future__ import annotations


class RiskResult:
    def __init__(
        self,
        passed: bool,
        reason: str = "",
        require_confirm: bool = False,
        require_force: bool = False,
    ):
        self.passed = passed
        self.reason = reason
        self.require_confirm = require_confirm
        self.require_force = require_force


def total_asset(state: dict) -> float:
    """总资产 = 现金 + 持仓市值。模拟模式无实时行情，按成本价估值。"""
    return state["cash"] + sum(
        p["cost"] * p["amount"] for p in state["positions"].values()
    )


def check_buy(cfg: dict, state: dict, code: str, amount: int, price: float) -> RiskResult:
    risk = cfg["risk"]
    assets = total_asset(state)
    cost = amount * price
    pos = state["positions"].get(code)
    new_value = (pos["cost"] * pos["amount"] if pos else 0) + cost
    if assets > 0 and new_value / assets > risk["max_single_stock_ratio"]:
        return RiskResult(
            False,
            f"单票市值 {new_value / assets:.1%} 超限 {risk['max_single_stock_ratio']:.0%}",
        )
    if cost > state["cash"]:
        return RiskResult(
            False, f"资金不足：需 {cost:.0f} 元，可用 {state['cash']:.0f} 元"
        )
    loss_limit = risk["max_daily_loss_ratio"] * assets
    if state["day_pnl"] <= -loss_limit:
        return RiskResult(
            False, f"当日亏损 {state['day_pnl']:.0f} 元已达上限，禁止买入"
        )
    require_confirm = assets > 0 and cost / assets >= risk["require_confirm_ratio"]
    return RiskResult(True, require_confirm=require_confirm)


def check_sell(cfg: dict, state: dict, code: str, amount: int, force: bool = False) -> RiskResult:
    risk = cfg["risk"]
    pos = state["positions"].get(code)
    if not pos:
        return RiskResult(False, f"无 {code} 持仓")
    if amount > pos["amount"]:
        return RiskResult(False, f"卖出 {amount} 股超过持仓 {pos['amount']} 股")
    if risk["forbid_all_sell"] and not force and amount == pos["amount"]:
        return RiskResult(False, "禁止一键清仓，需二次确认", require_force=True)
    return RiskResult(True)
