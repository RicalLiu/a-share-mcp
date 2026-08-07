"""订单执行：参数检查 -> 风控 -> 用户确认 -> 执行 -> 日志。"""
from __future__ import annotations

import datetime

from . import LOG, load_state, save_state
from .risk import RiskResult, check_buy, check_sell, total_asset

LOG_FILE = LOG / "trade.log"


def _log(action: str, code: str, amount: int, price, note: str, status: str) -> None:
    LOG.mkdir(exist_ok=True)
    line = (
        f"{datetime.datetime.now():%Y-%m-%d %H:%M}\n"
        f"{action}\n{code}\n{amount}股\n价格{price if price is not None else '市价'}\n"
        f"{note}\n{status}\n\n"
    )
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def _preview(state: dict, code: str, amount: int, price: float, risk: RiskResult, name: str = "") -> dict:
    assets = total_asset(state)
    cost = amount * price
    lines = [
        "交易确认：",
        f"股票：{name or code}",
        f"代码：{code}",
        f"数量：{amount}股",
        f"价格：{price:g}",
        f"预计金额：{cost:.0f}元",
        f"账户占比：{cost / assets:.1%}" if assets > 0 else "账户占比：-",
        f"风险：{'需重点确认' if risk.require_confirm else '正常'}",
    ]
    return {"status": "need_confirm", "preview": "\n".join(lines), "confirm": "确认交易"}


def buy_stock(cfg: dict, code: str, amount: int, price: float, name: str = "", confirm: bool = False) -> dict:
    if not (len(code) == 6 and code.isdigit()):
        return {"status": "rejected", "reason": "股票代码必须为 6 位数字"}
    if amount <= 0:
        return {"status": "rejected", "reason": "数量必须大于 0"}
    if price is None or price <= 0:
        return {"status": "rejected", "reason": "模拟模式需指定价格"}
    state = load_state()
    risk = check_buy(cfg, state, code, amount, price)
    if not risk.passed:
        return {"status": "rejected", "reason": risk.reason}
    if not confirm:
        return _preview(state, code, amount, price, risk, name)
    cost = amount * price
    pos = state["positions"].get(code)
    if pos:
        total_amount = pos["amount"] + amount
        pos["cost"] = round((pos["cost"] * pos["amount"] + cost) / total_amount, 4)
        pos["amount"] = total_amount
        if name:
            pos["name"] = name
    else:
        state["positions"][code] = {"name": name or "未知", "cost": price, "amount": amount}
    state["cash"] -= cost
    save_state(state)
    _log("BUY", code, amount, price, "用户确认", "SUCCESS")
    return {
        "status": "success",
        "code": code,
        "name": name or "未知",
        "amount": amount,
        "price": price,
        "cost": cost,
        "cash": state["cash"],
    }


def sell_stock(cfg: dict, code: str, amount: int, price: float | None = None, confirm: bool = False, force: bool = False) -> dict:
    if not (len(code) == 6 and code.isdigit()):
        return {"status": "rejected", "reason": "股票代码必须为 6 位数字"}
    if amount <= 0:
        return {"status": "rejected", "reason": "数量必须大于 0"}
    state = load_state()
    risk = check_sell(cfg, state, code, amount, force=force)
    if not risk.passed:
        if risk.require_force and not force:
            return {
                "status": "need_force_confirm",
                "preview": f"禁止一键清仓 {code}，请向用户二次确认后以 force=true 重试",
                "confirm": "确认清仓",
            }
        return {"status": "rejected", "reason": risk.reason}
    pos = state["positions"][code]
    settle = price if price is not None else pos["cost"]
    if not confirm:
        return _preview(state, code, amount, settle, risk, pos["name"])
    proceeds = amount * settle
    pnl = (settle - pos["cost"]) * amount
    state["cash"] += proceeds
    state["day_pnl"] = round(state["day_pnl"] + pnl, 2)
    pos["amount"] -= amount
    if pos["amount"] == 0:
        del state["positions"][code]
    save_state(state)
    _log("SELL", code, amount, settle, "用户确认", "SUCCESS")
    return {
        "status": "success",
        "code": code,
        "amount": amount,
        "price": settle,
        "proceeds": proceeds,
        "pnl": pnl,
        "cash": state["cash"],
    }


def cancel_order() -> dict:
    """撤单：模拟模式订单即时成交，无待撤订单。"""
    return {"status": "ok", "message": "模拟模式订单即时成交，无待撤订单"}
