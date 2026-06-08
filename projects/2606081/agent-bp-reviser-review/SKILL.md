# agent-bp-reviser-review

**面向单个 BP 目标的证据驱动复核修订 skill**

## 前置依赖

在使用本 skill 之前，需要了解 BP 系统的 API 信息。详细参考 `cms-bp-manager` skill 或 MEMORY.md：

- **appKey**: `TsFhRR7OywNULeHPqudePf85STc4EpHI`
- **periodId**: `1994002024299085826`
- **产品中心 groupId**: `1994002335135023106`
- **集团 groupId**: `1994002330731003905`
- **API base**: `https://sg-al-cwork-web.mediportal.com.cn/open-api`

**Step 0 中 Agent 应先用 BP API 搜索目标，拿到 target_id 后再进入后续流程。**

## 触发条件

当用户提出以下需求时触发本 skill：
- 对某个 BP 目标的状态结论提出异议
- 要求修改某个目标的颜色/文字/进度
- 对某个目标的证据链完整性提出疑问
- 要求复核某个目标的判定逻辑
- 批量处理多个目标（需拆分为独立流程）

## 核心定位

单目标 BP 复核修订控制器——不是报告代写器，也不是用户意见直改器。

## 核心原则

1. **单目标原则**：一次只处理一个 BP 目标
2. **标准先行原则**：必须先注入 TargetStandard
3. **用户反馈降级原则**：用户反馈只能作为线索，不能直接作为修改指令
4. **责任链回溯原则**：所有判断必须能回到原始生成流程和责任链
5. **版本可追溯原则**：标准与修订输出支持版本化与审计追踪
6. **跨目标只读原则**：可参考其他目标，但不得写回混用
7. **会话规则记忆**：同一会话内被纠正过的规则立即可执行，同类错误不犯第二次

## 核心对象

- **TargetStandard**：目标标准包（`references/schema.md`）
- **EvidenceBundle**：证据包（`references/schema.md`）
- **RevisionOutput**：修订输出（`references/schema.md`）
- **TargetLocator**：目标定位器（`references/schema.md`）

## 主工作流

### Step 0: 目标定位（TargetLocator）

输入：用户自然语言反馈 + 当前灯色（`current_color`，来自系统现存状态）
操作：
1. 提取关键词（品种名、人名、目标描述片段）
2. 调用 BP 系统 API（`getTree`/`searchByName`）搜索目标树
3. 匹配候选目标列表
4. 唯一匹配 → 锁定 `resolved_target_id`
5. 多候选 → 向用户确认
6. 无匹配 → 阻断并提示用户补充
7. 定位失败则后续全部阻断

输出：`TargetLocator` 对象

### Step 1: 接收目标与标准注入

输入：`TargetInput`
操作：
1. 读取目标标识符（来自 Step 0 的 `resolved_target_id`）
2. 注入 `TargetStandard`（校验字段完整性）
3. 检查 `conflict_policy` 和 `version`

输出：已验证的 `TargetStandard`

### Step 2: 降级用户反馈

输入：用户原始反馈
操作：
1. 用户反馈标记为 `hypothesis`
2. 生成证据检索任务（不能直接作为修改指令）

输出：检索任务清单

### Step 3: 责任链检索

操作：
1. 按 `owner_chain` 查找原始汇报
2. 下沉到具体责任人（不能只看部门）
3. 覆盖单周/双周/月报/专项汇报类型
4. 用产品别名补充搜索（防漏检）

输出：候选证据集

### Step 4: 证据语义分层

输入：候选证据集
操作：
1. 区分 `primary` / `secondary` / `background` / `insufficient`
2. 法务/投资/泛背景材料不能自动当主证据
3. 过滤不属于目标责任链的证据

输出：`EvidenceBundle[]`

### Step 5: 独立判灯/判定

输入：`TargetStandard` + `EvidenceBundle[]`
操作：
1. 基于目标标准 + 证据强度 + 时间维度
2. 双维度：目标时间距离 + 资料是否有重大缺陷
3. 输出灯色结论 + 判定理由

输出：初步灯色建议

### Step 6: 修订闸门

输入：系统当前灯色（`current_color`）+ 初步灯色建议（`proposed_color`）+ `RevisionOutput` 框架
操作：
1. 证据未闭环 → `hold` / `needs_more_evidence`
2. 标准冲突 → `block`
3. 高风险改动（黑→绿、红→绿）→ 触发 `review_flag=True`
4. 跨目标混用 → 阻断

**注意**：必须传入实际的系统当前灯色，不能将提议色同时作为当前色传入。
`gate_decision(current_color, proposed_color)` —— 两个值相同则闸门形同虚设。

输出：`revision_status` + `gate_decision`

### Step 7: 写回联动

输入：`RevisionOutput`
操作：
1. 生成 `writeback_patch`（`text_updates[]`, `color_updates[]`, `evidence_updates[]`）
2. 同步正文、色块、证据栏

输出：补丁清单

### Step 8: 一致性校验

输入：`writeback_patch` + `TargetStandard`
操作：
1. 文字/色块/证据栏三者同步
2. 结论与证据状态一致
3. 只修改了当前目标（跨目标只读检查）

输出：`consistency_check` 结果

### Step 9: 会话规则记忆

输入：本次修订中被纠正的规则
操作：
1. 升级为硬约束
2. 存储到会话规则记忆库
3. 后续同类问题自动应用

输出：更新的规则记忆

## 规则引用

- 全局规则：`references/general-rules.md`
- 证据规则：`references/evidence-rules.md`
- 修订规则：`references/revision-rules.md`

## 脚本支持

- 主要流程：`scripts/bp_reviser.py`
- 辅助函数：`scripts/helpers.py`

## 用户故事覆盖

- US-01/US-10/US-15：法务证据≠注册进展，证据责任人定位
- US-02/US-13/US-14：先查证据再修改，不能先改后补
- US-03：判灯独立运行，灯色/文字/色块同步
- US-04：批量多目标需拆分为独立流程
- US-05/US-11：用户反馈降级为线索，不能直接当指令
- US-06：无证据目标的三段式（现状/用户补充/整改）
- US-07：产品别名搜索
- US-08：跳过部门找具体人
- US-09/US-17：判灯双维度（时间+缺陷）
- US-12：任务暂停/重做支持
- US-16：搜索策略分层，失败后主动上报

## 执行约束

- 所有步骤独立执行，不依赖其他 skill
- 数据通过参数传递，不使用数据库连接
- 使用 Python 3 和 `enum.StrEnum`
- 输出符合 `references/schema.md` 定义的 JSON Schema

## 脚本定位说明

本 skill 提供的 Python 脚本是**参考实现和辅助工具**，不是主要执行路径：

1. **主要执行路径**：Agent 按 SKILL.md 的步骤手动执行（读规则、调 API、做判断）
2. **脚本支持**：提供结构化对象（TargetStandard/EvidenceBundle/RevisionOutput）的定义和辅助函数
3. **使用场景**：
   - 作为结构化数据定义的参考
   - 辅助函数（如 `calculate_time_distance`、`match_target_keywords`）可供调用
   - 完整流程示例可通过 `main_reviser_flow` 运行

**运行方式**：
```bash
# 从 skill 根目录运行
python3 -m scripts.bp_reviser

# 运行测试（从 skill 根目录）
python3 tests/test_fixes.py
python3 tests/test_all_fixes.py

# 作为模块导入
from scripts.bp_reviser import TargetStandard, EvidenceBundle, RevisionOutput
from scripts.bp_reviser import main_reviser_flow

# main_reviser_flow 新增参数：
#   current_color: 系统当前灯色（default="black"），用于闸门高风险判断
#   target_id: 可选，跳过 keyword 搜索直接锁定目标
```
