# stock-trading-mcp-agent

> 本地 A 股交易 MCP Server，让 AI Agent（Crush / Claude Code / Codex）安全调用同花顺交易能力。
> 当前为**模拟交易模式**，已预留真实券商通道接口。

## 简介

一个运行在本地电脑上的 A 股交易 MCP Server，通过标准 MCP 协议暴露账户查询、持仓查询、买卖下单、撤单能力，内置交易风控与用户确认机制，避免 Agent 绕过人工确认直接下单。

```
        AI Agent（Crush / Codex）
                 │
            MCP Protocol
                 │
      stock-trading-mcp-agent
         ┌───────┼───────┐
      Account  Risk  Trade
         │       │       │
      查询账户 交易检查 下单执行
                 │
        券商通道（模拟 / 待接入）
```

## 特性

- **MCP 标准协议**：基于 [FastMCP](https://gofastmcp.com)，即插即用
- **5 个交易工具**：`get_account` / `get_position` / `buy_stock` / `sell_stock` / `cancel_order`
- **强制确认机制**：任何买卖必须先返回确认预览，用户明确确认后才执行
- **内置风控**：单票占比上限、当日亏损熔断、大额交易重点确认、禁止一键清仓
- **完整交易日志**：每次成交记录到 `logs/trade.log`
- **双模式**：模拟模式开箱即用，真实通道接口已预留

## 目录结构

```
server.py              MCP Server 入口
config.yaml            模式与风控配置
mcp.json               标准 MCP 客户端配置示例
requirements.txt       依赖
tools/
  ├── account.py       账户查询
  ├── position.py      持仓查询
  ├── order.py         下单 / 撤单 / 日志
  └── risk.py          风控引擎
drivers/
  └── tonghuashun.py   同花顺驱动（预留接口）
data/portfolio.json    模拟账户状态（示例数据，请自行替换）
tests/test_smoke.py    冒烟自检
```

## 快速开始

```bash
pip install -r requirements.txt
python server.py            # 启动 MCP Server（stdio）
python tests/test_smoke.py  # 冒烟自检
```

## MCP 工具

| 工具 | 参数 | 说明 |
|------|------|------|
| `get_account()` | - | 现金 / 总资产 / 可用资金 / 当日盈亏 |
| `get_position()` | - | 持仓列表（代码 / 名称 / 数量 / 成本） |
| `buy_stock(code, amount, price, name?, confirm=false)` | 买入股票；`confirm=false` 返回确认预览 |
| `sell_stock(code, amount, price?, confirm=false, force=false)` | 卖出股票；一键清仓需 `force=true` 二次确认 |
| `cancel_order()` | - | 撤单（模拟模式无待撤订单） |

### 交易确认流程（强制）

任何买卖必须两步调用：

1. 先以 `confirm=false` 调用，返回交易确认预览（股票 / 代码 / 数量 / 价格 / 预计金额 / 账户占比 / 风险）
2. 向用户完整展示预览，等待用户**明确确认**后才以 `confirm=true` 调用执行

一键清仓（卖出全部持仓）返回 `need_force_confirm`，需向用户二次确认后以 `force=true` 调用。

### 风控规则（config.yaml `risk`）

| 规则 | 默认值 | 行为 |
|------|--------|------|
| `max_single_stock_ratio` | 0.2 | 单票市值超过总资产 20% 拒绝 |
| `max_daily_loss_ratio` | 0.03 | 当日亏损达总资产 3% 禁止买入 |
| `require_confirm_ratio` | 0.05 | 单笔金额 ≥ 总资产 5% 标记「需重点确认」 |
| `forbid_all_sell` | true | 禁止一键清仓，需二次确认 |

## 接入 AI Agent

### Crush

```bash
mcp add stock-trader --type stdio --command python --args "/path/to/stock-trading-mcp-agent/server.py"
```

### 标准 MCP 客户端（mcp.json）

将 `mcp.json` 中 `server.py` 路径替换为实际路径后放入客户端配置。

### Agent System Prompt

```
你是我的A股交易助手。你可以调用stock-trader MCP。规则：
1. 任何交易必须经过risk检查。
2. 任何真实交易必须获得用户明确确认。
3. 交易前必须展示：股票、代码、数量、价格、金额、风险。
4. 禁止自行扩大交易数量。
5. 禁止连续交易。
6. 所有交易必须记录日志。
```

## 切换到真实交易

1. 将 `config.yaml` 中 `mode` 改为 `real`
2. 实现 `drivers/tonghuashun.py`（或新增券商驱动，如 QMT `xtquant`），接口：`login` / `get_account` / `get_position` / `buy` / `sell` / `cancel`
3. 先小额实盘验证，再正式使用

## 合规与免责声明

- 程序化交易 A 股需遵守券商协议与《程序化交易管理规定》；高频交易需向券商报备
- 本项目仅提供技术框架，不构成投资建议；因使用本项目造成的任何损失由使用者自行承担
- 真实交易前请确认券商是否允许程序化交易

## License

[MIT](LICENSE)
