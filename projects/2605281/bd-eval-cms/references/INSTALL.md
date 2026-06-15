# bd-eval-cms 安装与使用说明

> **版本**：v0.10.4（2026-06-15）
> **适配**：玄关开放平台 CMS 业务（深康/德镁/维盛/院外业务中心/天津康哲/康联达）
> **Skill 路径**：`agent-factory/projects/2605281/bd-eval-cms/`

---

## 一、Skill 是什么

bd-eval-cms 是 Agent Factory 出品的 CMS 业务投前评估 Skill，专门用于：

- 业务主体（深康/德镁/维盛/天津康哲/院外业务中心/康联达）下产品引进、BD 工作
- 投前评估报告（Gate 0~5 全流程）
- 报告 HTML 渲染 + 玄关知识库归档

它内部做了完整的工作流编排（Phase 1-6）、Gate 评估、互斥规则校验、文档产出。

---

## 二、安装

### 2.1 全新安装

```bash
# 1. clone 仓库（sparse-checkout 只取这一个 skill）
git clone --depth 1 --sparse https://github.com/evan-zhang/agent-factory.git
cd agent-factory
git sparse-checkout set projects/2605281/bd-eval-cms

# 2. 验证目录
ls projects/2605281/bd-eval-cms/
# 应该看到：SKILL.md  config.yaml  scripts/  references/  templates/
```

Skill 目录：`agent-factory/projects/2605281/bd-eval-cms/`

### 2.2 已有旧版升级

```bash
cd /path/to/agent-factory
git pull origin master
git sparse-checkout set projects/2605281/bd-eval-cms
```

---

## 三、必填配置（执行前必看）

> **重要**：bd-eval-cms 缺配置不会静默走默认值——执行时会主动提示，配置完才能继续。

### 3.1 系统级 AppKey（必填）

**用途**：把报告归档到玄关知识库（产品引进知识库空间）。

**申请/获取方式**：联系玄关开放平台 admin 开「系统级 AppKey」（注意：是 BP 流水线系统级 key，不是个人 cowork key）。

**配置位置**：`projects/2605281/bd-eval-cms/.secrets/kb_appkey`

**写入步骤**：

```bash
SKILL=projects/2605281/bd-eval-cms

# 1. 创建 .secrets 目录（被 .gitignore 忽略，不入仓）
mkdir -p "$SKILL/.secrets"

# 2. 写入 AppKey（替换成你的实际 AppKey）
echo -n '你的系统级AppKey' > "$SKILL/.secrets/kb_appkey"

# 3. 验证
cat "$SKILL/.secrets/kb_appkey"
# 应输出 32 字节左右的字符串，无前后空白
```

**安全约束**：
- 文件路径 `**/.secrets/` 已在 `.gitignore` 忽略，不会进 git
- 不要把 AppKey 写到 config.yaml 或其他会入仓的文件
- 不要用环境变量（`XG_BIZ_API_KEY` / `DOCVIEWER_KB_APPKEY`）——bd-eval-cms 是后台 BP 流水线，必须用系统级文件凭证

### 3.2 config.yaml 知识库参数（已预填）

`projects/2605281/bd-eval-cms/config.yaml` 已包含业务固定参数，开箱即用：

```yaml
knowledgeBase:
  appKeyFile: ".secrets/kb_appkey"        # 必填项 3.1 配的就是这个文件
  projectId: "2060176831872499713"        # 玄关产品引进知识库空间 ID（业务固定）
  rootDir: "CPYJ"                          # 知识库根目录
  pathTemplate: "{ROOT}/{YYYYMM}/{caseCode}"
  format: "html"
  previewTtlYears: 5
```

> **注意**：`projectId` 和 `rootDir` 是 CMS 评估业务专用的空间定位参数，**不要改**。

### 3.3 OpenClaw 主框架（必填）

bd-eval-cms 是 OpenClaw 生态的 Skill，必须在 OpenClaw 环境下运行：

- ✅ OpenClaw 已安装：`~/.openclaw/` 目录存在
- ✅ OpenClaw gateway 在运行
- ✅ Skill 通过 OpenClaw 加载

如果 OpenClaw 没装，参考官方文档：https://docs.openclaw.ai

---

## 四、配置校验

装完跑一次健康检查，确认所有必填项都到位：

```bash
bash projects/2605281/bd-eval-cms/scripts/bd-eval-cms-health-check.sh
```

**期望输出**：`✅ 20  ⚠️ 1  ❌ 0`（20 通过 + 1 提示 + 0 失败 = 就绪）

如果出现 ❌，按提示补齐：
- `❌ AppKey 文件` → 走 3.1 步骤
- `❌ curl/python3` → 装系统工具
- `❌ search/* 脚本` → sparse-checkout 没勾上，重做 2.1 第 1 步

---

## 五、使用方法

### 5.1 入口：单条商机评估

```bash
# 方式 A：参数式
bash projects/2605281/bd-eval-cms/scripts/run-opportunity.sh \
  --product "TRTL-729" \
  --company "TestCo Pharma"

# 方式 B：JSON 文件式
bash projects/2605281/bd-eval-cms/scripts/run-opportunity.sh \
  --json /path/to/opportunity.json

# 方式 C：从 stdin 读 JSON
echo '{"product":"X","company":"Y"}' | bash run-opportunity.sh --json -
```

参考 JSON 模板：`projects/2605281/bd-eval-cms/references/opportunity.example.json`

### 5.2 内部流程（无需手动介入）

`run-opportunity.sh` 是唯一对外入口，内部自动完成：

1. **Phase 1** DISCOVERY — 公司/产品/适应症初步信息收集
2. **Phase 2** 深度尽调 + Gate 0~5 评估
3. **Phase 3-4** 业务主体互斥校验 + 财务硬门槛
4. **Phase 5** 报告生成（`04-final-report.md`）
5. **Phase 5.5** preflight 检查 + 知识库归档
6. **Phase 6** 完成

### 5.3 报告渲染（独立调用）

```bash
# 默认 Style A1（推荐）
bash projects/2605281/bd-eval-cms/scripts/render_report.sh <品种目录>

# 指定风格
bash render_report.sh <品种目录> 12 mckinsey-navy
bash render_report.sh <品种目录> 13
bash render_report.sh <品种目录> a1 investment-blue
```

### 5.4 知识库归档（独立调用）

```bash
# 单独跑归档（报告已生成后）
bash projects/2605281/bd-eval-cms/scripts/sync-to-knowledge-base.sh <品种目录>
```

> 正常情况不用手动调，Phase 5.5 会自动调。

### 5.5 测试套件（回归用）

```bash
SKILL=projects/2605281/bd-eval-cms

bash $SKILL/scripts/bd-eval-cms-health-check.sh           # 健康检查
bash $SKILL/scripts/test-run-opportunity.sh                # 端到端测试
bash $SKILL/scripts/search/validate_gate_search.sh --test  # 搜索门控测试
bash $SKILL/scripts/test-preflight-phase.sh                # 前置条件测试
```

**期望**：
- health-check: 20✅1⚠️0❌
- test-run-opportunity: 19/19
- validate_gate_search --test: 5/5
- test-preflight: 6/6

---

## 六、参数缺失时会发生什么

bd-eval-cms **不会**静默走默认值。执行过程中如果发现必填参数缺失，会**主动停下来提示**：

### 6.1 检测点 1：AppKey 文件缺失

执行 `sync-to-knowledge-base.sh` 时：

```
❌ 错误：未找到 AppKey 文件: .../bd-eval-cms/.secrets/kb_appkey
   请创建该文件并写入系统级 AppKey：
     mkdir -p ".../bd-eval-cms/.secrets"
     echo -n '你的AppKey' > ".../bd-eval-cms/.secrets/kb_appkey"
```

**修复**：走 3.1 步骤

### 6.2 检测点 2：AppKey 为空

```
❌ 错误：AppKey 文件为空: .../bd-eval-cms/.secrets/kb_appkey
   请写入有效的系统级 AppKey
```

**修复**：`echo -n '实际值' > .secrets/kb_appkey`

### 6.3 检测点 3：config.yaml 缺关键字段

```
❌ 错误：config.yaml 中未配置 knowledgeBase.projectId
```

**修复**：检查 `config.yaml` 的 `knowledgeBase` 段是否完整

### 6.4 检测点 4：OpenClaw 未装

`bd-eval-cms-health-check.sh` 会标 ❌ 并提示。

### 6.5 检测点 5：缺商机参数

`run-opportunity.sh` 没传 `--product` / `--company` / `--json`：

```
❌ 错误：必须提供 --product + --company，或 --json <path|->，或 --json -
```

**修复**：按 5.1 选一种方式传参

---

## 七、目录结构

```
projects/2605281/bd-eval-cms/
├── SKILL.md                              # 技能主文档
├── config.yaml                           # 业务固定配置
├── version.json                          # 版本元数据
├── .secrets/
│   └── kb_appkey                         # AppKey（不入仓，本地配置）
├── scripts/
│   ├── run-opportunity.sh                # 【入口】单条商机评估
│   ├── orchestrator-resume.sh            # 续跑
│   ├── preflight-phase.sh                # Phase 5.5 前置检查
│   ├── render_report.sh                  # 报告渲染
│   ├── sync-to-knowledge-base.sh         # 知识库归档
│   ├── bd-eval-cms-health-check.sh       # 健康检查
│   ├── test-run-opportunity.sh           # 端到端测试
│   ├── test-preflight-phase.sh           # 前置条件测试
│   ├── archive-links.sh                  # 链接归档
│   └── search/                           # 搜索子系统（v0.10.0 起自包含）
│       ├── core_search.sh
│       ├── field_extractor.sh
│       ├── keyword_mapper.sh
│       ├── source_ranker.sh
│       ├── validate_gate_search.sh
│       └── lib/                          # 搜索 lib
├── references/
│   ├── INSTALL.md                        # 【本文件】安装使用说明
│   ├── SOP.md                            # 业务 SOP
│   ├── WORKFLOW-OVERVIEW.md              # 流程概览
│   ├── sub-agent-prompt-template.md      # 子 Agent 提示词模板
│   ├── opportunity.example.json          # 商机参数示例
│   └── A-0 ~ E-1                         # 业务 profile 模板
└── templates/
    ├── style-12/                         # 风格 12 渲染
    ├── style-13/                         # 风格 13 渲染
    └── style-a1/                         # 风格 A1 渲染（推荐）
```

---

## 八、升级日志

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| v0.10.4 | 2026-06-15 | 术语表列错位修复 + 章节编号 11+ 显示中文修复 |
| v0.10.3 | 2026-06-14 | AppKey 来源改 skill 专享文件 `.secrets/kb_appkey` |
| v0.10.2 | 2026-06-14 | P0/P1/P2 同链路修复（健康检查 + 知识库归档 + yq 去除） |
| v0.10.1 | 2026-06-14 | Issue #75 test-preflight fixture 修复 |
| v0.10.0 | 2026-06-14 | 搜索能力完全内化（不依赖 multi-search） |
| v0.9.4.2 | 2026-06-13 | Issue #74 P2 health-check multi-search 误报修复 |
| v0.9.4.1 | 2026-06-13 | 终审反馈修复（商机 ID 视为不透明 token） |
| v0.9.4 | 2026-06-13 | 外部商机 ID 接入 + 知识库路径重构 + pypinyin 清除 |
| v0.9.3 | 2026-06-12 | 终审 + 三轮 reviewer 复盘 + 案例数据清理 |

---

## 九、问题反馈

遇到问题先去 [GitHub Issues](https://github.com/evan-zhang/agent-factory/issues) 看有没有同类。

**新 Issue 模板**：

```
标题：[bd-eval-cms] <一句话描述>

环境：
- bd-eval-cms 版本：v0.x.x
- OpenClaw 版本：v0.x.x
- 操作系统：macOS / Linux

复现步骤：
1. ...
2. ...

期望：...
实际：...

日志/截图：
```

---

_最后更新：2026-06-15 · bd-eval-cms v0.10.4_
