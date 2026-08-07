"""模拟账户状态读写（data/portfolio.json）。"""
from __future__ import annotations

import datetime
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
LOG = BASE / "logs"

DEFAULT_STATE = {
    "cash": 500000.0,
    "positions": {"600519": {"name": "贵州茅台", "cost": 1500.0, "amount": 100}},
    "day": datetime.date.today().isoformat(),
    "day_pnl": 0.0,
}


def load_state() -> dict:
    DATA.mkdir(exist_ok=True)
    path = DATA / "portfolio.json"
    if not path.exists():
        state = json.loads(json.dumps(DEFAULT_STATE))
        save_state(state)
        return state
    state = json.loads(path.read_text(encoding="utf-8"))
    today = datetime.date.today().isoformat()
    if state.get("day") != today:
        state["day"] = today
        state["day_pnl"] = 0.0
    return state


def save_state(state: dict) -> None:
    DATA.mkdir(exist_ok=True)
    (DATA / "portfolio.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )
