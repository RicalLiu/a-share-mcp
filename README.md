# a-share-mcp

> 本地 A 股交易 MCP Server，让 AI Agent（Crush / Claude Code / Codex）安全调用同花顺交易能力。
> 当前为**模拟交易模式**，已预留真实券商通道接口，可平滑升级。

---

## ⚠️ 安装前必读：许可证

本项目采用 **GPL v2+ 与 LGPL v2.1+ 双许可证**，**任选其一**：

- **GPL v2+**：适用于整体衍生作品，你的作品必须以 GPL 开源
- **LGPL v2.1+**：适用于作为库链接进你的程序，仅库本身的修改需开源

> [!IMPORTANT]
> 两种许可证都具有 **copyleft 传染性**：你对本项目的任何修改，**一旦分发（发给别人 / 公开发布 / 部署给第三方），必须同步开源并提供完整源代码**。不允许闭源分发本项目或其衍生作品。
>
> 详细说明与选择指引见 [LICENSE](LICENSE)，协议全文见 `LICENSE.GPLv2` 与 `LICENSE.LGPLv2.1`。

---

## 简介

一个运行在本地电脑上的 A 股交易 MCP Server。通过标准 MCP 协议暴露账户查询、持仓查询、买卖下单、撤单能力，内置交易风控与**强制用户确认机制**，防止 AI Agent 绕过人工确认直接下单。

```
        AI Agent（Crush / Codex）
                 │
            MCP Protocol
                 │
         a-share-mcp（本服务）
         ┌───────┼───────┐
      Account  Risk  Trade
         │       │       │
      查询账户 交易检查 下单执行
                 │
        券商通道（模拟 / 待接入）
```

## 功能特性

- **标准 MCP 协议**：基于 [FastMCP](https://gofastmcp.com)，即插即用，兼容主流 AI Agent
- **5 个交易工具**：`get_account` / `get_position` / `buy_stock` / `sell_stock` / `cancel_order`
- **强制确认机制**：任何买卖必须先返回确认预览（股票 / 代码 / 数量 / 价格 / 金额 / 账户占比 / 风险），用户明确确认后才执行；一键清仓需二次确认
- **内置风控引擎**：单票占比上限、当日亏损熔断、大额交易重点确认、禁止一键清仓，规则可配置
- **完整交易日志**：每次成交记录到 `logs/trade.log`，格式固定、可审计
- **双模式**：模拟模式开箱即用；真实券商通道接口已预留，升级不改 MCP 层

## 目录结构

```
.
├── server.py              MCP Server 入口
├── config.yaml            模式与风控配置
├── mcp.json               标准 MCP 客户端配置示例
├── requirements.txt       依赖清单
├── LICENSE                双许可证说明（GPL v2+ / LGPL v2.1+）
├── LICENSE.GPLv2          GPL v2 全文
├── LICENSE.LGPLv2.1       LGPL v2.1 全文
├── tools/
│   ├── account.py         账户查询
│   ├── position.py        持仓查询
│   ├── order.py           下单 / 撤单 / 交易日志
│   └── risk.py            风控引擎
├── drivers/
│   └── tonghuashun.py     券商驱动（预留接口）
├── data/portfolio.json    模拟账户状态（示例数据，请自行替换）
├── tests/test_smoke.py    冒烟自检
└── logs/                  交易日志（运行时生成，不入库）
```

## 系统要求

- Windows（真实交易自动化目标平台；模拟模式任意平台可运行）
- Python 3.11+
- 模拟模式仅需 `fastmcp`

## 安装

```bash
git clone git@github.com:RicalLiu/a-share-mcp.git
cd a-share-mcp
pip install -r requirements.txt
```

> 安装即视为已阅读并接受 [LICENSE](LICENSE) 中 GPL v2+ 与 LGPL v2.1+ 双许可证的任选其一约定。

## 快速开始

```bash
# 1. 启动 MCP Server（stdio 模式，供 AI Agent 调用）
python server.py

# 2. 冒烟自检（不启动服务，直接验证交易全流程）
python tests/test_smoke.py
```

预期输出 `SMOKE OK`。

## 录入你的持仓

模拟账户状态保存在 `data/portfolio.json`，直接编辑即可：

```json
{
  "cash": 500000.0,
  "positions": {
    "600519": {"name": "贵州茅台", "cost": 1500.0, "amount": 100}
  },
  "day": "2026-08-07",
  "day_pnl": 0.0
}
```

| 字段 | 含义 |
|------|------|
| `cash` | 可用现金，参与风控计算（总资产 = 现金 + Σ 成本 × 股数） |
| `positions` | 持仓：代码 → 名称 / 成本价（每股）/ 股数 |
| `day` / `day_pnl` | 当日已实现盈亏，跨日自动清零，可留默认值 |

## MCP 工具

| 工具 | 参数 | 说明 |
|------|------|------|
| `get_account()` | - | 现金 / 总资产 / 可用资金 / 当日盈亏 |
| `get_position()` | - | 持仓列表（代码 / 名称 / 数量 / 成本） |
| `buy_stock(code, amount, price, name?, confirm=false)` | 买入股票；`confirm=false` 返回确认预览 |
| `sell_stock(code, amount, price?, confirm=false, force=false)` | 卖出股票；一键清仓需 `force=true` 二次确认 |
| `cancel_order()` | - | 撤单（模拟模式订单即时成交，无待撤订单） |

### 返回示例

`get_account()`：

```json
{"cash": 500000.0, "total_asset": 650000.0, "available": 500000.0,
 "positions_value": 150000.0, "day_pnl": 0.0}
```

`buy_stock()` 未确认时（`confirm=false`）：

```json
{
  "status": "need_confirm",
  "preview": "交易确认：\n股票：贵州茅台\n代码：600519\n数量：100股\n价格：1500\n预计金额：150000元\n账户占比：23.1%\n风险：需重点确认",
  "confirm": "确认交易"
}
```

## 交易确认流程（强制，不可跳过）

任何买卖必须两步调用：

1. 先以 `confirm=false` 调用 → 返回 `need_confirm` 预览（含股票 / 代码 / 数量 / 价格 / 预计金额 / 账户占比 / 风险）
2. 向用户完整展示预览，等待用户**明确确认**后，以 `confirm=true` 调用执行

一键清仓（卖出全部持仓）返回 `need_force_confirm`，需向用户二次确认后以 `force=true` 调用。

未确认的交易一律不成交，不会写日志、不会改动账户状态。

## 风控规则

由 `config.yaml` 的 `risk` 段配置，服务端强制，Agent 不可绕过：

| 规则 | 默认值 | 行为 |
|------|--------|------|
| `max_single_stock_ratio` | 0.2 | 单票市值超过总资产 20% 拒绝买入 |
| `max_daily_loss_ratio` | 0.03 | 当日已实现亏损达总资产 3% 禁止买入（卖出止损不受限） |
| `require_confirm_ratio` | 0.05 | 单笔金额 ≥ 总资产 5% 标记「需重点确认」 |
| `forbid_all_sell` | true | 禁止一键清仓，需 `force=true` 二次确认 |

```
mode: simulation  # simulation（模拟）| real（真实，待接入）
risk:
  max_single_stock_ratio: 0.2
  max_daily_loss_ratio: 0.03
  require_confirm_ratio: 0.05
  forbid_all_sell: true
```

## 交易日志

每次成交写入 `logs/trade.log`：

```
2026-08-07 10:30
BUY
300750
100股
价格220
用户确认
SUCCESS
```

## 接入 AI Agent

### Crush

```bash
mcp add stock-trader --type stdio --command python --args "/path/to/a-share-mcp/server.py"
```

### 标准 MCP 客户端

将 `mcp.json` 中 `server.py` 路径替换为实际路径后，放入客户端配置。

### Agent System Prompt（建议粘贴给你的 Agent）

```
你是我的A股交易助手。你可以调用stock-trader MCP。规则：
1. 任何交易必须经过risk检查。
2. 任何真实交易必须获得用户明确确认。
3. 交易前必须展示：股票、代码、数量、价格、金额、风险。
4. 禁止自行扩大交易数量。
5. 禁止连续交易。
6. 所有交易必须记录日志。
```

## 预留接口

`drivers/tonghuashun.py` 已定义券商驱动接口（Step 3 待实现），MCP 层、风控层、确认流程均不依赖具体实现：

```python
class Tonghuashun:
    def login(self)                                  # 登录
    def get_account(self)                            # 查询账户
    def get_position(self)                           # 查询持仓
    def buy(self, code, amount, price=None)          # 买入
    def sell(self, code, amount, price=None)         # 卖出
    def cancel(self, order_id=None)                  # 撤单
```

实现任一券商通道只需：新建驱动类实现上述接口，并在 `order.py` 中按 `config.yaml` 的 `mode` 分流到真实驱动即可，MCP 工具签名与调用方不变。

## 后续开发方案（路线图）

### 1. 同花顺客户端自动化驱动（近期）
- 用 `pyautogui` + `pywin32` + `opencv-python` + `pytesseract` 操作同花顺客户端（川财 / 华安证券版）
- 流程：打开客户端 → 登录 → 进入交易页 → 输入代码 / 数量 → 点击买入 / 卖出 → OCR 读取成交结果
- 前置条件：本机安装同花顺客户端、已登录券商账户
- 依赖已注释在 `requirements.txt`，取消注释即可安装

### 2. 券商量化通道（推荐长期方案）
- **华安证券**：官网正式提供「华安证券 QMT 极速策略交易平台」，支持 Python 策略编程；优先确认是否可开通 **miniQMT**（外部 Python API `xtquant`），可脱离界面纯脚本下单。门槛约 50 万，以客户经理答复为准
- **川财证券**：官网未公开提供 QMT / Ptrade，需联系客户经理确认量化通道
- 实现方式：新增 `drivers/qmt.py`（基于 `xtquant`），接口与预留驱动一致，MCP 层零改动
- 合规：程序化交易需遵守券商协议与《程序化交易管理规定》，首次开展需向券商报告；高频（>300 笔/秒）需额外报备

### 3. 行情接入
- 模拟模式目前按成本价估值；接入行情源（如本地行情数据接口 / 实时行情库）后支持真实市值与盈亏计算

### 4. 高级交易能力
- 条件单 / 止损单 / 网格策略：在 `tools/order.py` 之上扩展，风控与确认流程复用
- 多账户支持：将 `data/portfolio.json` 扩展为按账户分目录

## 合规与免责声明

- 本项目仅提供技术框架，不构成投资建议；使用本项目进行真实交易的风险由使用者自行承担
- 程序化交易 A 股须遵守券商协议与《程序化交易管理规定》，高频交易需向券商报备
- 真实交易前请确认你的券商是否允许程序化交易

## License

**GPL v2+ 或 LGPL v2.1+，任选其一**（见 [LICENSE](LICENSE)）。

- 修改后分发必须开源（copyleft）
- 全文：`LICENSE.GPLv2`（GPL v2+）、`LICENSE.LGPLv2.1`（LGPL v2.1+）
