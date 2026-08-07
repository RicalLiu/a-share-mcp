"""A 股交易 MCP Server（FastMCP）。

默认模拟模式（config.yaml mode: simulation）；接入同花顺后切换 mode: real。
"""
from __future__ import annotations

from pathlib import Path

import yaml
from fastmcp import FastMCP

from tools import account, order, position

BASE = Path(__file__).resolve().parent
cfg = yaml.safe_load((BASE / "config.yaml").read_text(encoding="utf-8"))

mcp = FastMCP("stock-trader")


@mcp.tool
def get_account() -> dict:
    """查询账户：现金、总资产、可用资金。"""
    return account.get_account()


@mcp.tool
def get_position() -> list:
    """查询当前持仓。"""
    return position.get_position()


@mcp.tool
def buy_stock(code: str, amount: int, price: float, name: str = "", confirm: bool = False) -> dict:
    """买入股票。confirm=False 返回交易确认预览；用户确认后以 confirm=True 执行。"""
    return order.buy_stock(cfg, code, amount, price, name=name, confirm=confirm)


@mcp.tool
def sell_stock(code: str, amount: int, price: float | None = None, confirm: bool = False, force: bool = False) -> dict:
    """卖出股票。一键清仓需 force=True 二次确认。"""
    return order.sell_stock(cfg, code, amount, price=price, confirm=confirm, force=force)


@mcp.tool
def cancel_order() -> dict:
    """撤单（模拟模式订单即时成交，无待撤订单）。"""
    return order.cancel_order()


if __name__ == "__main__":
    mcp.run()
