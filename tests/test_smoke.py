"""冒烟自检：模拟买入/卖出/风控/日志全流程。运行：python tests/test_smoke.py"""
import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import DATA, load_state, save_state
from tools import account, order, position

CFG = {
    "mode": "simulation",
    "risk": {
        "max_single_stock_ratio": 0.2,
        "max_daily_loss_ratio": 0.03,
        "require_confirm_ratio": 0.05,
        "forbid_all_sell": True,
    },
}


def main():
    backup = (DATA / "portfolio.json").read_text(encoding="utf-8")
    try:
        save_state(
            {"cash": 500000.0, "positions": {}, "day": datetime.date.today().isoformat(), "day_pnl": 0.0}
        )

        # 买入：未确认只给预览
        r = order.buy_stock(CFG, "600519", 60, 1500, name="贵州茅台")
        assert r["status"] == "need_confirm" and "交易确认" in r["preview"], r

        # 确认后成交
        r = order.buy_stock(CFG, "600519", 60, 1500, name="贵州茅台", confirm=True)
        assert r["status"] == "success" and r["cash"] == 410000.0, r

        # 单票超 20% 拒绝（现有 90000 + 新增 45000 = 135000 / 500000 = 27%）
        r = order.buy_stock(CFG, "600519", 30, 1500, confirm=True)
        assert r["status"] == "rejected" and "超限" in r["reason"], r

        # 卖出：未确认给预览
        r = order.sell_stock(CFG, "600519", 40)
        assert r["status"] == "need_confirm", r

        # 部分卖出成交
        r = order.sell_stock(CFG, "600519", 40, confirm=True)
        assert r["status"] == "success" and r["cash"] == 470000.0, r

        # 一键清仓需 force 二次确认
        r = order.sell_stock(CFG, "600519", 20, confirm=True)
        assert r["status"] == "need_force_confirm", r
        r = order.sell_stock(CFG, "600519", 20, confirm=True, force=True)
        assert r["status"] == "success" and r["cash"] == 500000.0, r

        # 当日亏损熔断：亏损超 3% 后禁止买入
        state = load_state()
        state["day_pnl"] = -20000.0
        save_state(state)
        r = order.buy_stock(CFG, "000001", 100, 10, confirm=True)
        assert r["status"] == "rejected" and "亏损" in r["reason"], r

        # 账户与持仓一致性
        state = load_state()
        assert account.get_account()["total_asset"] == state["cash"], account.get_account()
        assert position.get_position() == [], position.get_position()
        assert order.cancel_order()["status"] == "ok"

        print("SMOKE OK")
    finally:
        (DATA / "portfolio.json").write_text(backup, encoding="utf-8")


if __name__ == "__main__":
    main()
