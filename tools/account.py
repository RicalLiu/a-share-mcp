from __future__ import annotations

from . import load_state
from .risk import total_asset


def get_account() -> dict:
    """查询账户：现金、总资产、可用资金。"""
    state = load_state()
    assets = total_asset(state)
    return {
        "cash": state["cash"],
        "total_asset": assets,
        "available": state["cash"],
        "positions_value": assets - state["cash"],
        "day_pnl": state["day_pnl"],
    }
