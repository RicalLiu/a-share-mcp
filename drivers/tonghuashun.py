"""同花顺客户端自动化驱动（预留接口，对应 paymeplan.md Step 3）。

真实模式（config.yaml mode: real）下，通过 pyautogui / pywin32 /
opencv-python / pytesseract 操作同花顺客户端完成登录、查询、买卖与撤单。
当前仅定义接口，未实现。
"""


class Tonghuashun:
    def login(self):
        raise NotImplementedError("同花顺驱动尚未实现（Step 3）")

    def get_account(self):
        raise NotImplementedError("同花顺驱动尚未实现（Step 3）")

    def get_position(self):
        raise NotImplementedError("同花顺驱动尚未实现（Step 3）")

    def buy(self, code, amount, price=None):
        raise NotImplementedError("同花顺驱动尚未实现（Step 3）")

    def sell(self, code, amount, price=None):
        raise NotImplementedError("同花顺驱动尚未实现（Step 3）")

    def cancel(self, order_id=None):
        raise NotImplementedError("同花顺驱动尚未实现（Step 3）")
