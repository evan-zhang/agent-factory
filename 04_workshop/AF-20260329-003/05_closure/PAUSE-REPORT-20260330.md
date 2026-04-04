# AF-20260329-003 阶段暂停报告

> **项目**：BP价值拆解与归因评分系统
> **状态**：PAUSED（暂停）
> **暂停时间**：2026-03-30
> **下次继续时**：待 Evan 确认三层结构权重分配方案

---

## 一、项目概述

### 1.1 项目来源

- 来源：三省工作台 TPR-20260329-001
- 交付物：BP价值拆解与归因评分系统

### 1.2 核心目标

通过 AI 辅助，对产品中心的 BP（Business Plan）进行价值评分，按目标负责人统计得分，支撑绩效评估。

### 1.3 当前状态

| 模块 | 状态 | 说明 |
|------|------|------|
| API 连通性 | ✅ 完成 | BP周期/组织/任务树/目标详情 |
| 数据拉取 | ✅ 完成 | 10个BP，完整KR和承接人 |
| Agent 评分 | ✅ 完成 | `--agent-score` 模式 |
| 报告生成 | ✅ 完成 | Markdown 格式 |
| 三层结构权重分配 | ⏸️ **暂停** | 待确认方案 |

---

## 二、技术进展记录

### 2.1 API 路径修复

**问题**：三方交付代码中的 API 路径不完整，导致 401 错误。

**解决**：
- 正确路径：`/bp/task/v2/getGoalAndKeyResult`
- 认证方式：`AppKey: TsFhRR7OywNULeHPqudePf85STc4EpHI`

**经验教训**（已记入 RULES.md 第十六章）：
- 调用玄关系 API 前，必须先查 dev-guide 仓库官方文档
- 不信任第三方代码中的 API 路径

### 2.2 字段映射修复

**问题**：代码期望字段名与 API 返回不一致。

| 代码期望 | API 实际返回 |
|---------|------------|
| `bpId` | `id` |
| `objective` | `name` |
| `measures` | `keyResults[].actions` |

### 2.3 Agent 评分模式

**实现**：新增 `--agent-score` 参数

```bash
# 第一步：拉取数据，生成 bp-list.json
python3 scripts/main.py run --org "产品中心" --period "2026年度计划BP" --agent-score

# 第二步：Agent 评分后写入 bp-scores.json
# 第三步：重新运行，生成报告
python3 scripts/main.py run --org "产品中心" --period "2026年度计划BP" --agent-score
```

**原因**：外部 LLM API（公司 AI Router / ZAI）调用不稳定，采用 Agent 内置模型更可靠。

### 2.4 承接人提取

**最终方案**（已实现）：
- 从 `taskUsers` 中提取 `role="承接人"` 的 `empList`
- 递归遍历所有层级（BP → KR → actions → downTaskList → ...）
- 按 action 数量分配 BP 分数

---

## 三、BP 三层结构分析（核心发现）

### 3.1 层级对应关系

```
BP（目标）
  └── KR（成果）
       └── 举措 = 下一层级的"目标"（递归）
              └── KR（下一层级的成果）
                   └── 举措 = 再下一层级的"目标"
                          └── ...
```

**关键发现**：
- 上一层级的"举措" = 下一层级的"目标"
- 层级之间通过"举措→目标"的映射递归连接
- 递归深度越深，越接近最终执行

### 3.2 每层责任人角色

| 层级 | 角色 | 说明 |
|------|------|------|
| 目标层 | 责任人/负责人 | 战略方向把控 |
| 成果层 | 责任人/负责人 | 里程碑分解 |
| 举措层 | 承接人 | 具体执行落地 |

### 3.3 API 数据示例

```json
{
  "name": "确保产品稳定输出，实现年度上市得分7分...",
  "taskUsers": [{"role": "承接人", "empList": [{"name": "林刚"}]}],
  "keyResults": [
    {
      "name": "完成签约管线产品上市目标，确保得分≥3.5分",
      "taskUsers": [{"role": "承接人", "empList": [{"name": "林刚"}]}],
      "actions": [
        {
          "name": "德昔度司他（1分）：2月获批",
          "taskUsers": [{"role": "承接人", "empList": [{"name": "史哲"}, {"name": "袁超"}]}]
        }
      ]
    }
  ]
}
```

---

## 四、分数分配方案讨论

### 4.1 方案对比

| 方案 | 描述 | 问题 |
|------|------|------|
| 方案A | 三层分别按 40%/30%/30% | 同一人获得叠加分数 |
| 方案B | 三层合并，按参与度平均 | 未体现战略责任差异 |
| **方案C** | 按深度分配递增权重 | 待确认 |

### 4.2 建议的方案C（待确认）

按递归深度分配（越深权重越高）：

```
深度1（BP本身的目标层）：20%
深度2（第一层举措 = 第二层目标）：25%
深度3（第二层举措 = 第三层目标）：30%
深度4+：25%（递减）
```

**示例**：BP1 得 18 分
- 林刚（深度1）：18 × 20% = **3.6 分**
- 史哲（深度2）：18 × 25% = **4.5 分**

---

## 五、当前代码状态

### 5.1 文件结构

```
04_workshop/AF-20260329-003/
├── 04_execution/
│   └── workspace/
│       ├── scripts/
│       │   ├── main.py           # CLI主入口
│       │   ├── bp_fetcher.py     # BP数据拉取
│       │   ├── scorer.py         # AI评分（已修改支持anthropic格式）
│       │   ├── report.py         # 报告生成
│       │   ├── adjuster.py       # 人工调整
│       │   └── bonus_checker.py  # 奖金审查
│       ├── config/
│       │   └── scoring_weights.yaml
│       └── output/
│           ├── 产品中心-20260330-report.md  # 最新报告
│           └── bp-list.json       # BP数据（供Agent评分）
└── 05_closure/
    └── PAUSE-REPORT-20260330.md  # 本文档
```

### 5.2 关键代码修改

**bp_fetcher.py 新增函数**：
```python
def get_acceptor_action_counts(bp_detail: dict) -> dict:
    """递归统计每个承接人在该BP中参与的action数量"""
```

**main.py 新增参数**：
```python
run_parser.add_argument("--agent-score", action="store_true")
```

**report.py 修改**：
- 新增 KR（关键成果）展示
- 个人得分汇总按人名汇总
- HTML 标签清理

---

## 六、已验证可用的功能

### 6.1 数据拉取 ✅

```bash
export BP_APP_KEY="TsFhRR7OywNULeHPqudePf85STc4EpHI"
export BP_BASE_URL="https://sg-al-cwork-web.mediportal.com.cn/open-api"

# 获取产品中心10个BP
python3 scripts/main.py run --org "产品中心" --period "2026年度计划BP" --agent-score
```

### 6.2 报告生成 ✅

报告包含：
- BP 评分排名（总分100分）
- 每个 BP 的关键成果（KR）
- 每个 BP 的承接人分解（按 action 数量）
- 个人得分汇总表

### 6.3 Agent 评分 ✅

当前使用 Agent 内置模型进行评分，不依赖外部 API。

---

## 七、下次继续时的任务

### 7.1 必须完成（P0）

- [ ] 确认三层结构的权重分配方案（方案C或自定义）
- [ ] 修改 `get_acceptor_action_counts()` 支持按深度统计
- [ ] 修改分数分配逻辑，按深度和权重计算
- [ ] 更新报告模板，展示三层承接人

### 7.2 建议完成（P1）

- [ ] 协办人（role="协办人"）是否需要统计？
- [ ] 报告优化：显示承接人来源层级（目标层/成果层/举措层）
- [ ] 分数调整功能支持按层级调整

### 7.3 后续功能（P2）

- [ ] LLM API 稳定后，恢复自动评分（当前 `--agent-score` 是临时方案）
- [ ] 支持多周期对比
- [ ] 支持跨组织对标

---

## 八、关键配置

| 配置项 | 值 |
|-------|-----|
| BP Base URL | `https://sg-al-cwork-web.mediportal.com.cn/open-api` |
| AppKey | `TsFhRR7OywNULeHPqudePf85STc4EpHI` |
| 产品中心 groupId | `1994002335135023106` |
| 2026年度计划 BP periodId | `1994002024299085826` |
| API 路径 | `/bp/task/v2/getGoalAndKeyResult` |

---

## 九、参考文档

- BP 系统 API 说明：`02.产品业务AI文档/BP/BP系统API说明.md`（dev-guide 仓库）
- 工作协同 API 说明：`02.产品业务AI文档/工作协同/工作协同API说明.md`

---

## 十、附录

### A. 个人得分汇总（当前版本）

| 排名 | 姓名 | 总分 | BP数量 |
|-----|------|------|--------|
| 1 | 史哲 | 19.1分 | 9个BP |
| 2 | 康璐琪 | 16.5分 | 10个BP |
| 3 | 陆融 | 13.4分 | 8个BP |
| 4 | 林刚 | 10.5分 | 10个BP |
| 5 | 袁超 | 10.3分 | 8个BP |
| 6 | 王敏 | 7.7分 | 5个BP |
| 7 | 吴三燕 | 6.3分 | 7个BP |
| 8 | 姜非 | 6.2分 | 4个BP |
| 9 | 伊慧 | 4.5分 | 6个BP |
| 10 | 付忠明 | 3.4分 | 3个BP |
| 11 | 彭怀政 | 2.3分 | 4个BP |

> 注：此汇总按 action 数量分配，未区分层级权重。

---

*文档生成时间：2026-03-30 08:15*
*下次继续时请先阅读本文档*
