# 外部依赖清单

## 必需依赖

### 1. OpenClaw 环境
- **用途**：运行时环境（cron系统、skill加载、message推送）
- **安装**：`npm install -g openclaw`
- **文档**：https://docs.openclaw.ai

### 2. longbridge CLI
- **用途**：行情获取、交易执行、基本面数据
- **安装**：
  ```bash
  # macOS
  brew tap longbridgeapp/tap && brew install longbridgeapp/tap/longbridge
  # 或直接下载
  curl -sSL https://github.com/longbridgeapp/longbridge-cli/releases/latest/download/longbridge-cli-darwin-arm64.zip -o lb.zip
  unzip lb.zip && sudo mv longbridge /usr/local/bin/
  ```
- **配置**：需要 longbridge 证券账户
  ```bash
  longbridge config set --app_key YOUR_KEY --app_secret YOUR_SECRET --access_token YOUR_TOKEN
  ```
- **验证**：`longbridge quote 9926.HK --format json`

### 3. longbridge 子 Skills（127个）
- **用途**：细分数据获取（行情、资金流、财报、分析师预期等）
- **位置**：`~/.agents/skills/longbridge-*/`
- **安装**：随 quant workspace 一起部署
- **关键子 Skill**：
  - `longbridge-quote` — 实时行情
  - `longbridge-news` — 新闻资讯
  - `longbridge-fundamental` — 基本面数据
  - `longbridge-capital-flow` — 资金流向
  - `longbridge-earnings` — 财报数据
  - `longbridge-kline` — K线数据
  - `longbridge-depth` — 盘口深度

### 4. .env 配置文件
- **默认位置**：`/Users/evan/.openclaw/gateways/life/domains/quant/.env`
- **覆盖方式**：`dry_run_orchestrator.py discovery --longbridge-env <path>`
- **必需变量**：
  ```bash
  # 长桥证券 API
  LONGBRIDGE_APP_KEY=xxx
  LONGBRIDGE_APP_SECRET=xxx
  LONGBRIDGE_ACCESS_TOKEN=xxx
  ```

### 5. OpenClaw 工具
- **web_search** — 新闻/催化搜索
- **message** — Telegram 推送
- **cron** — 定时任务调度

### 6. Python 运行依赖
- **pandas-market-calendars**：production calendar source
- **pytest**：本地测试套件
- **验证**：
  ```bash
  cd {PROJECT_ROOT}
  PYTHONPATH=src/scripts .venv/bin/python -m pytest -q
  ```

## 可选依赖

### 7. TradingAgents（多空辩论引擎）
- **用途**：C阶段多空辩论（替代同LLM三角色辩论）
- **位置**：`{WORKDIR}/engines/TradingAgents/`
- **依赖**：Python 3.10+、tradingagents 包、各LLM API Key
- **说明**：不可用时自动回退到同LLM辩论，不影响核心功能

## 部署检查清单

```bash
# 1. 检查 longbridge CLI
longbridge --version

# 2. 检查 .env
source /Users/evan/.openclaw/gateways/life/domains/quant/.env && echo $LONGBRIDGE_ACCESS_TOKEN | head -c 10

# 3. 测试行情
longbridge quote 9926.HK --format json

# 3b. 测试 stock-picking live quote discovery
PYTHONPATH=src/scripts .venv/bin/python src/scripts/dry_run_orchestrator.py \
  --event-root /tmp/stock-picking-smoke/events \
  --registry src/strategies/registry.yaml \
  --custom-refs src/strategies/custom_refs.yaml \
  discovery --caller cron --market US --strategy-id taroc --strategy-version 1.0.0 \
  --run-mode discovery --timezone America/New_York --universe-ref us_default \
  --calendar-source production_calendar --signal-date 2026-06-24 \
  --market-data-source longbridge_quote --universe-symbols AAPL.US MSFT.US \
  --idempotency-key stock-picking-smoke

# 4. 检查 Skills
ls ~/.agents/skills/longbridge-quote/SKILL.md
ls ~/.agents/skills/stock-picking-v2/SKILL.md

# 5. 检查 OpenClaw
openclaw status
```
