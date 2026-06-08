# agent-bp-reviser-review

**面向单个 BP 目标的证据驱动复核修订 skill**

## 概述

这是一个用于 BP（Business Planning）系统目标修订的 skill，基于证据驱动的复核修订流程，确保目标状态修订的准确性和一致性。

## 核心特性

- ✓ **单目标处理**：一次只处理一个 BP 目标
- ✓ **标准先行**：所有修订必须先注入 TargetStandard
- ✓ **证据驱动**：基于证据检索和分层进行修订决策
- ✓ **责任链回溯**：所有判断可追溯到原始生成流程
- ✓ **版本可追溯**：支持版本化和审计追踪
- ✓ **跨目标只读**：可参考其他目标，但不得写回混用
- ✓ **会话规则记忆**：同类错误不犯第二次

## 目录结构

```
agent-bp-reviser-review/
├── SKILL.md                    # 核心执行入口（9步工作流）
├── version.json                # 元数据
├── README.md                   # 本文件
├── references/
│   ├── api-reference.md        # 输入输出接口定义
│   ├── general-rules.md        # 全局规则（15条）
│   ├── evidence-rules.md       # 证据规则（12条）
│   ├── revision-rules.md       # 修订规则（15条）
│   └── schema.md               # 完整 JSON Schema 定义
├── scripts/
│   ├── bp_reviser.py           # 主要处理流程
│   └── helpers.py              # 辅助函数
├── examples/
│   ├── target_standard_sample.json
│   ├── evidence_bundle_sample.json
│   ├── revision_output_sample.json
│   └── end_to_end_sample.md    # 端到端示例
└── tests/
    ├── run_all.py                       # 统一测试入口（unittest）
    ├── test_standard_injection.{md,py}  # 标准注入（规格+可执行）
    ├── test_evidence_scoping.{md,py}    # 证据分层
    ├── test_revision_gating.{md,py}     # 修订闸门
    ├── test_writeback_consistency.{md,py} # 写回一致性
    ├── test_bp_api_integration.py       # BP API mock 测试（无需网络）
    ├── test_fixes.py                    # 早期修复验证（脚本式）
    └── test_all_fixes.py                # 完整修复验证（脚本式）
```

## 快速开始

### 1. 执行示例

```bash
cd ~/.openclaw/skills/agent-bp-reviser-review
python3 scripts/bp_reviser.py
```

### 2. 测试辅助函数

```bash
python3 scripts/helpers.py
```

### 3. 查看端到端示例

```bash
cat examples/end_to_end_sample.md
```

## 核心工作流

### Step 0: 目标定位
- 提取用户反馈中的关键词
- 搜索 BP 系统目标树
- 匹配并锁定目标

### Step 1: 标准注入
- 读取 TargetStandard
- 校验字段完整性
- 检查版本和冲突策略

### Step 2: 降级用户反馈
- 用户反馈标记为假设
- 生成证据检索任务

### Step 3: 责任链检索
- 按责任链搜索原始汇报
- 下沉到具体责任人
- 覆盖多种汇报类型

### Step 4: 证据语义分层
- 区分 primary / secondary / background / insufficient
- 法务/投资材料不能作为进展证据
- 过滤不属于责任链的证据

### Step 5: 独立判灯/判定
- 基于目标标准 + 证据强度 + 时间维度
- 双维度：目标时间距离 + 资料缺陷
- 输出灯色结论 + 判定理由

### Step 6: 修订闸门
- 证据未闭环 → hold / needs_more_evidence
- 高风险改动 → 触发复核
- 标准冲突 → block

### Step 7: 写回联动
- 生成 writeback_patch
- 同步正文、色块、证据栏

### Step 8: 一致性校验
- 文字/色块/证据栏三者同步
- 结论与证据状态一致
- 只修改了当前目标

### Step 9: 会话规则记忆
- 被纠正的规则升级为硬约束
- 同类错误不犯第二次

## 核心对象

### TargetStandard（目标标准包）

```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "target_name": "完成3个新品种注册",
  "layer": "goal",
  "bp_type": "organization",
  "period": {"start": "2026-01-01", "end": "2026-03-31"},
  "owner": "张三",
  "responsibility_chain": ["公司", "研发部", "张三"],
  "version": "1.0.0",
  "conflict_policy": "prefer_latest"
}
```

### EvidenceBundle（证据包）

```json
{
  "evidence_id": "ev_001",
  "evidence_type": "goal_report",
  "evidence_level": "primary",
  "evidence_source": "周报-2026-W23-张三",
  "evidence_confidence": 0.85,
  "responsibility_chain": ["公司", "研发部", "张三"]
}
```

### RevisionOutput（修订输出）

```json
{
  "target_code": "ORG_2026_Q1_REG_001",
  "revision_status": "approved",
  "revision_action": "rewrite",
  "revision_reason": "基于责任人周报证据，目标进展良好",
  "consistency_check": {"passed": true, "issues": []},
  "writeback_patch": {
    "text_updates": [...],
    "color_updates": [...],
    "evidence_updates": [...]
  }
}
```

## 用户故事覆盖

| 用户故事 | 描述 | 覆盖文件 |
|----------|------|----------|
| US-01, US-10, US-15 | 法务证据≠注册进展，证据责任人定位 | evidence-rules.md |
| US-02, US-13, US-14 | 先查证据再修改，不能先改后补 | revision-rules.md |
| US-03 | 判灯独立运行，灯色/文字/色块同步 | revision-rules.md |
| US-04 | 批量多目标需拆分为独立流程 | general-rules.md |
| US-05, US-11 | 用户反馈降级为线索，不能直接当指令 | revision-rules.md |
| US-06 | 无证据目标的三段式（现状/用户补充/整改） | revision-rules.md |
| US-07 | 产品别名搜索 | evidence-rules.md |
| US-08 | 跳过部门找具体人 | evidence-rules.md |
| US-09, US-17 | 判灯双维度（时间+缺陷） | revision-rules.md |
| US-12 | 任务暂停/重做支持 | revision-rules.md |
| US-16 | 搜索策略分层，失败后主动上报 | evidence-rules.md |

## 规则体系

### 全局规则（15条）
- GR-01: 单目标强制原则
- GR-02: 标准先行原则
- GR-03: 用户反馈降级原则
- GR-04: 责任链回溯原则
- GR-05: 版本可追溯原则
- GR-06: 跨目标只读原则
- GR-07: 会话规则记忆原则
- GR-08: 证据层级强制原则
- GR-09: 判灯独立性原则
- GR-10: 一致性强制原则
- GR-11: 写回补丁原则
- GR-12: 闸门决策原则
- GR-13: 搜索策略分层原则
- GR-14: 任务暂停/重做支持原则
- GR-15: 无证据目标三段式原则

### 证据规则（12条）
- ER-01: 法务证据≠注册进展
- ER-02: 先查证据再修改
- ER-03: 产品别名搜索
- ER-04: 跳过部门找具体人
- ER-05: 证据责任人定位
- ER-06: 证据时间维度
- ER-07: 重大缺陷过滤
- ER-08: 证据层级强制区分
- ER-09: 汇报类型覆盖
- ER-10: 证据置信度计算
- ER-11: 证据排除规则
- ER-12: 证据范围备注

### 修订规则（15条）
- RR-01: 修订闸门决策
- RR-02: 修订动作分类
- RR-03: 用户反馈降级处理
- RR-04: 判灯双维度
- RR-05: 灯色/文字/色块同步
- RR-06: 批量多目标拆分
- RR-07: 无证据目标三段式
- RR-08: 任务暂停/重做支持
- RR-09: 搜索策略分层
- RR-10: 写回补丁生成
- RR-11: 一致性校验
- RR-12: 会话规则记忆
- RR-13: 跨目标只读检查
- RR-14: 修订理由强制
- RR-15: 置信度更新

## 依赖项

- Python 3.6+
- 无外部依赖（标准库）

## 测试

### 运行全部单元测试（推荐）

```bash
cd ~/.openclaw/skills/agent-bp-reviser-review
python3 tests/run_all.py        # 37 个 unittest 用例（规格 28 + API mock 9）
```

### 单独运行某一套

```bash
python3 tests/test_standard_injection.py     # 标准注入 7 用例
python3 tests/test_evidence_scoping.py       # 证据分层 7 用例
python3 tests/test_revision_gating.py        # 修订闸门 8 用例
python3 tests/test_writeback_consistency.py  # 写回一致性 6 用例
python3 tests/test_bp_api_integration.py     # BP API mock 9 用例（无需网络）
```

### 早期脚本式测试（独立运行）

```bash
python3 tests/test_fixes.py
python3 tests/test_all_fixes.py
```

### 端到端示例

```bash
python3 -c "
from scripts.bp_reviser import main_reviser_flow
import json

sample_feedback = '把「完成3个新品种注册」改成绿色'
sample_target = json.load(open('examples/target_standard_sample.json'))
sample_evidence = [json.load(open('examples/evidence_bundle_sample.json'))]

result = main_reviser_flow(sample_feedback, sample_target, sample_evidence)
print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
"
```

## 版本信息

- **当前版本**: 1.0.0
- **创建日期**: 2026-06-06
- **作者**: BP System Team
- **类型**: bp-revision-controller
- **类别**: single-target-revision

## 许可证

内部使用

---

## 联系方式

如有问题或建议，请联系 BP System Team。
