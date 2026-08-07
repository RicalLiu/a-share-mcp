from __future__ import annotations

from . import load_state


def get_position() -> list:
    """查询持仓列表。"""
    state = load_state()
    return [
        {"code": code, "name": p["name"], "amount": p["amount"], "cost": p["cost"]}
        for code, p in state["positions"].items()
    ]
