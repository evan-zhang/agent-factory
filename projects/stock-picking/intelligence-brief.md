# 原始情报收集 — stock-picking 项目

**日期**：2026-06-23
**用途**：收编 stock-picking-v2 + serenity-skill 时的完整分析记录

---

## 一、stock-picking-v2 原始状态

**位置**：`~/.agents/skills/stock-picking-v2/`
**版本**：v2.0（未纳入 Factory）
**文件清单**（11 个）：

```
SKILL.md                          # 入口：系统架构、三市场cron、数据目录、风控红线
DEPENDENCIES.md                   # 依赖：longbridge CLI + 127子skill + .env
flows/discovery.md                # 初选流程：TAROC五步法完整执行步骤
flows/validation.md               # 复选流程：3天2次确认入池
flows/weekly-review.md            # 周复盘流程：W1-W4追踪+清理建议
references/taroc-methodology.md   # TAROC方法论核心（ARK+段永平+冯柳+O'Neil）
references/data-schema.md         # 6个CSV的完整字段定义
holidays/a_share.yaml             # A股休市日（32行，文本描述非结构化）
holidays/hk_share.yaml            # 港股休市日（51行）
holidays/us_share.yaml            # 美股休市日（50行）
scripts/position-monitor.py       # Python持仓监控+移动止损脚本
```

### 已发现的问题

| # | 问题 | 严重性 | 收编修复计划 |
|---|------|--------|------------|
| 1 | holidays/*.yaml 是文本说明，不是真正的 YAML 数据结构 | 必修 | S4 改为结构化日期列表 |
| 2 | position-monitor.py 硬编码 fallback 路径 | 必修 | S4 参数化 |
| 3 | 缺少 VERSION 文件 | 必修 | S4 创建 |
| 4 | 缺少 CHANGELOG | 建议 | S8 补齐 |
| 5 | 缺少 verification/dry-run 测试 | 建议 | S5 补齐 |
| 6 | cron 调度写在 SKILL.md 里，与 skill 逻辑耦合 | 必修 | 架构重构，剥离到 Gateway |
| 7 | 选股策略与交易系统绑死，不可替换 | 必修 | 架构重构，拆分层级 |

### 核心数据结构（6个CSV）

1. **drafts_{market}.csv** — 初选草稿（15字段）
2. **candidates_{market}.csv** — 正式候选（17字段，含W1-W4周度表现）
3. **four_week_tracker_{market}.csv** — 四周追踪（9字段）
4. **target_pool.csv** — 建仓目标池（10字段）
5. **positions.csv** — 持仓记录（21字段，含移动止损状态机）
6. **trade_log.csv** — 交易日志
7. **trading_state.csv** — 交易状态（冷却期/高水位线）

### 风控规则（硬编码红线）

- 买入必须人工确认（不可修改）
- 卖出零人工干预（不可修改）
- 止损不可跳过（不可修改）
- 移动止损：-8%初始 → >5%保本 → >10%锁5% → >15%锁10% → >20%锁15%
- 组合回撤>20% → 全清 + 冷却期（系统性10日/个股5日）
- 双重确认：第一次触发后等5分钟，第二次仍触发才执行
- dry_run 默认 true

---

## 二、serenity-skill（卡脖子选股框架）原始状态

**位置**：`/Users/evan/.openclaw/gateways/life/domains/quant/skills/serenity-skill/`
**名称**：chockpoint-investor / serenity-skill
**文件清单**（13 个）：

```
SKILL.md                          # 核心方法论：BOM拆解→三高→时机→龙头→崩塌条件
lead-scanner.md                   # 线索扫描引擎（5类信号源→趋势校验→交叉过滤→BOM衔接）
reverse-engine.md                 # 逆向引擎（个股→评分+邻居节点）
case-study.md                     # 完整实战范例（2026-06-03全市场盲扫）
industries/semiconductor-photonics.md  # AI光子学7层卡脖子地图
industries/ev-battery.md          # 新能源电池产业链
industries/energy-storage.md      # 储能产业链
industries/consumer-goods.md      # 消费品产业链
industries/biotech-cdmo.md        # 生物医药CDMO产业链
references/thesis-risks.md        # 框架局限性+批评+风险
references/track-record.md        # Serenity公开战绩记录
README.md
```

### 方法论核心

**五步流程**：
1. BOM 树拆解（找供应商数量突变层）
2. 三高筛选（高增长=供需失衡、高壁垒=五维打分≥3、高利润=验证指标）
3. 时机判断（机构未定价 vs 即将被定价的催化剂）
4. 龙头定位（最难被绕开的那一家）
5. 崩塌条件（论点和工具崩塌分开判断）

**三种引擎**：
- 正向（lead-scanner）：趋势→公司，5类信号源自动扫描
- 逆向（reverse-engine）：个股→评分+邻居节点
- 横向扩展：以个股为坐标扫描上下游同层替代链

**输出规范**：
- 写入 `data/research/` 目录
- 聊天摘要≤20行
- 明确声明"研究起点，不触发建仓"
- 与 TAROC 流程衔接（research → TAROC 升级为 draft）

### 与 stock-picking 的关系

| 维度 | serenity-skill | stock-picking-v2 |
|------|---------------|-----------------|
| 定位 | 研究框架 | 交易系统 |
| 触发 | 用户主动调用 | cron 定时 |
| 时间维度 | 一次性分析 | 持续追踪（天/周） |
| 数据持久化 | research 文件 | drafts/candidates CSV |
| 风控 | 无 | 完整（止损+回撤+冷却） |
| 交易执行 | 明确不做 | 买入人工确认，卖出自动 |
| 方法论深度 | 产业链级别拆解 | 综合评分体系 |

---

## 三、确认的架构重构方案

### 原则

> cron 不在 skill 里。选股策略可替换。复选/追踪/持仓监控/止损都可独立拎出来。用 SOP 流程串在一起。

### 三层架构

```
Layer 1: stock-picking (SOP编排层)
    ↓ 调用
Layer 2: 独立能力模块（可插拔）
    ├── taroc-strategy        (策略)
    ├── chokepoint-strategy   (策略，来自serenity)
    ├── selection-validation  (通用)
    ├── position-tracker      (通用)
    └── position-monitor      (通用)
    ↓ 共用
Layer 3: 共享基础设施
    ├── holidays/             (交易日历)
    ├── data-schema           (CSV结构定义)
    └── scripts/              (可执行脚本)
```

### 各模块边界

**stock-picking（master SOP）**
- 定义完整生命周期流程
- 编排各模块调用顺序
- 定义数据流转规范
- 不含任何策略实现

**taroc-strategy**
- TAROC 五步法（T→A→R→O→C）
- 输入：市场+日期
- 输出：draft 候选清单（写入 drafts CSV）

**chokepoint-strategy**
- BOM 拆解 + 三高筛选 + lead-scanner + reverse-engine
- 输入：市场+日期 或 用户指定的行业/个股
- 输出：draft 候选清单（写入 drafts CSV，格式与 taroc 一致）

**selection-validation**
- 3天2次复选逻辑
- 输入：drafts CSV
- 输出：更新 drafts + 确认入 candidates

**position-tracker**
- 四周追踪 + 周复盘报告
- 输入：candidates + tracker CSV
- 输出：周报 + 清理建议

**position-monitor**
- 持仓监控 + 移动止损 + 组合风控
- 输入：positions CSV + 实时行情
- 输出：止损指令 + 状态更新
- 含 position-monitor.py 脚本

### serenity-skill 的 industries/ 和 references/ 处理

- `industries/` → 移入 chokepoint-strategy 的参考资料
- `case-study.md` → chokepoint-strategy 的使用示例
- `references/thesis-risks.md` → chokepoint-strategy 的风险提示
- `references/track-record.md` → 仅供参考，不纳入发布版

---

## 四、版本规划

- 首版：v1.0.0（首次纳入 Factory 管理体系）
- 原始 v2.0 历史在 CHANGELOG 的 Pre-factory 段落记录
- semver 规则：major=架构变更，minor=新策略/模块，patch=修复

---

## 五、待决问题

1. [ ] 各子模块是独立 skill 还是 stock-picking 的子目录？（S3 决定）
2. [ ] data/ 目录统一放在哪？（master skill vs 各模块各自管理）
3. [ ] Gateway cron 配置具体怎么配？（从 skill 剥离后的调度方案）
4. [ ] 是否保留 TradingAgents 可选依赖？
