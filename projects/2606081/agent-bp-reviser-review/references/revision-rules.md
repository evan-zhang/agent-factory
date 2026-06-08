# 修订规则

## RR-01: 修订闸门决策

**规则**：高风险改动必须触发闸门决策。

**高风险场景**：
- 黑→绿（`black` → `green`）
- 红→绿（`red` → `green`）
- 证据未闭环
- 标准冲突

**闸门动作**：
- `block`: 阻断修订
- `hold`: 暂停修订
- `needs_more_evidence`: 需要更多证据
- `approved`: 批准修订

**决策逻辑**：
```python
def gate_decision(revision_output):
    # 高风险改动触发复核
    if is_high_risk_change(revision_output):
        revision_output.review_flag = True
        return "hold", "需要人工复核"
    
    # 证据未闭环
    if not evidence_closed(revision_output):
        return "needs_more_evidence", "证据未闭环"
    
    # 标准冲突
    if has_conflict(revision_output):
        return "block", "标准冲突"
    
    # 通过
    return "approved", "批准修订"
```

**用户故事**：US-05, US-11

---

## RR-02: 修订动作分类

**规则**：修订必须明确动作类型。

**动作类型**：
- `rewrite`: 重写内容
- `keep`: 保持不变
- `revert`: 回退到之前状态
- `mark_pending`: 标记为待处理

**动作选择**：
```python
def determine_revision_action(current_state, proposed_state, evidence_strength):
    # 证据强 + 状态不同 → rewrite
    if evidence_strength > 0.8 and current_state != proposed_state:
        return "rewrite", "证据充分，修订状态"
    
    # 证据弱 → mark_pending
    if evidence_strength < 0.5:
        return "mark_pending", "证据不足，待处理"
    
    # 状态相同 → keep
    if current_state == proposed_state:
        return "keep", "状态一致，保持不变"
    
    # 其他 → revert
    return "revert", "回退到原状态"
```

---

## RR-03: 用户反馈降级处理

**规则**：用户反馈只能作为线索，不能直接作为修改指令。

**降级流程**：
1. 用户反馈 → 标记为 `hypothesis`
2. 生成证据检索任务
3. 检索结果验证假设
4. 验证通过才执行修订

**降级代码**：
```python
def downgrade_user_feedback(raw_feedback):
    return {
        "hypothesis": raw_feedback,
        "status": "pending_verification",
        "search_tasks": generate_search_tasks(raw_feedback)
    }
```

**用户故事**：US-05, US-11

---

## RR-04: 判灯双维度

**规则**：判灯必须基于时间维度 + 缺陷维度双维度。

**时间维度**：
- 目标时间距离（距离目标结束时间）
- 证据时间相关性

**缺陷维度**：
- 资料是否有重大缺陷
- 证据完整性

**判灯逻辑**：
```python
def determine_light_color(target_standard, evidence_bundle):
    # 时间距离
    time_distance = calculate_time_distance(target_standard)
    
    # 缺陷检测
    has_major_defects = detect_major_defects(evidence_bundle)
    
    # 绿灯：时间近 + 无缺陷
    if time_distance < 30 and not has_major_defects:
        return "green", "时间临近，无重大缺陷"
    
    # 黄灯：时间中等 或 有轻微缺陷
    if time_distance < 90 or not has_major_defects:
        return "yellow", "时间中等或存在轻微缺陷"
    
    # 红灯：时间远 或 有重大缺陷
    if time_distance >= 90 or has_major_defects:
        return "red", "时间较远或存在重大缺陷"
    
    # 黑灯：无证据
    if len(evidence_bundle.primary) == 0:
        return "black", "无有效证据"
```

**用户故事**：US-09, US-17

---

## RR-05: 灯色/文字/色块同步

**规则**：判灯结果必须与文字和色块同步。

**同步检查**：
```python
def sync_consistency_check(revision_output):
    issues = []
    
    # 检查文字与灯色一致
    if text_color_mismatch(revision_output):
        issues.append("文字与灯色不一致")
    
    # 检查色块与灯色一致
    if block_color_mismatch(revision_output):
        issues.append("色块与灯色不一致")
    
    # 检查证据栏与证据包一致
    if evidence_mismatch(revision_output):
        issues.append("证据栏与证据包不一致")
    
    return len(issues) == 0, issues
```

**用户故事**：US-03

---

## RR-06: 批量多目标拆分

**规则**：批量多目标必须拆分为独立流程。

**拆分逻辑**：
```python
def split_batch_targets(batch_input):
    flows = []
    for target in batch_input.targets:
        flow = {
            "target_id": target.target_id,
            "target_name": target.target_name,
            "status": "pending",
            "dependencies": []
        }
        flows.append(flow)
    return flows
```

**执行约束**：
- 每个目标独立执行
- 不共享状态
- 独立输出 `RevisionOutput`

**用户故事**：US-04

---

## RR-07: 无证据目标三段式

**规则**：无证据目标必须按三段式处理。

**三段式模板**：
```markdown
## 现状

当前目标无有效证据。

## 用户补充

请提供以下信息：
- 目标责任人
- 目标进展情况
- 相关支持材料

## 整改计划

- [ ] 收集目标证据
- [ ] 验证责任人汇报
- [ ] 更新目标状态
```

**触发条件**：
```python
if len(evidence_bundle.primary) == 0:
    return generate_three_segment_output()
```

**用户故事**：US-06

---

## RR-08: 任务暂停/重做支持

**规则**：必须支持任务暂停和重做。

**状态管理**：
```python
def pause_task(task_id):
    task_state = {
        "task_id": task_id,
        "status": "paused",
        "checkpoint": get_current_checkpoint(),
        "timestamp": now()
    }
    save_state(task_state)
    return task_state

def resume_task(task_id):
    task_state = load_state(task_id)
    if task_state.status != "paused":
        raise Error("任务未暂停，无法恢复")
    restore_checkpoint(task_state.checkpoint)
    return task_state
```

**用户故事**：US-12

---

## RR-09: 搜索策略分层

**规则**：证据搜索必须按策略分层，失败后主动上报。

**搜索层次**：
1. 精确匹配（目标编码）
2. 模糊匹配（目标名称）
3. 别名搜索（产品别名）
4. 责任人搜索

**失败上报**：
```python
def search_with_fallback(target_standard):
    strategies = [
        exact_match_search,
        fuzzy_match_search,
        alias_search,
        responsibility_search
    ]
    
    for strategy in strategies:
        results = strategy(target_standard)
        if results:
            return results
    
    # 全部失败，上报
    report_search_failure(target_standard, strategies)
    return []
```

**用户故事**：US-16

---

## RR-10: 写回补丁生成

**规则**：所有写回必须通过 `writeback_patch` 结构化补丁。

**补丁结构**：
```python
def generate_writeback_patch(revision_output):
    patch = {
        "text_updates": [],
        "color_updates": [],
        "evidence_updates": []
    }
    
    # 文字更新
    if revision_output.revision_action == "rewrite":
        patch.text_updates.append({
            "field": "target_description",
            "old_value": current_description,
            "new_value": new_description
        })
    
    # 色块更新
    if color_changed:
        patch.color_updates.append({
            "target": revision_output.target_code,
            "old_color": current_color,
            "new_color": new_color
        })
    
    # 证据更新
    if evidence_changed:
        patch.evidence_updates.append({
            "evidence_id": evidence_id,
            "action": "add|remove|update",
            "details": evidence_details
        })
    
    return patch
```

---

## RR-11: 一致性校验

**规则**：写回前必须通过一致性校验。

**校验项目**：
1. 文字/色块/证据栏三者同步
2. 结论与证据状态一致
3. 只修改了当前目标（跨目标只读检查）

**校验代码**：
```python
def consistency_check(revision_output, target_standard):
    issues = []
    
    # 检查文字/色块/证据栏同步
    if not sync_check(revision_output):
        issues.append("文字/色块/证据栏不同步")
    
    # 检查结论与证据一致
    if not conclusion_evidence_match(revision_output):
        issues.append("结论与证据不一致")
    
    # 检查跨目标写回
    if cross_target_writeback_detected(revision_output):
        issues.append("检测到跨目标写回")
    
    return {
        "passed": len(issues) == 0,
        "issues": issues
    }
```

---

## RR-12: 会话规则记忆

**规则**：被纠正过的规则升级为硬约束，同类错误不犯第二次。

**记忆机制**：
```python
def remember_corrected_rule(rule_id, correction):
    session_memory[rule_id] = {
        "original_rule": rule_id,
        "correction": correction,
        "timestamp": now(),
        "applied": False
    }

def apply_session_memory(revision_output):
    for rule_id, memory in session_memory.items():
        if not memory["applied"]:
            apply_correction(memory["correction"])
            memory["applied"] = True
```

---

## RR-13: 跨目标只读检查

**规则**：可参考其他目标，但不得写回混用。

**检查代码**：
```python
def check_cross_target_writeback(writeback_patch, current_target_code):
    for update in writeback_patch.text_updates:
        if update.get("target") != current_target_code:
            return True, "检测到跨目标文字写回"
    
    for update in writeback_patch.color_updates:
        if update.get("target") != current_target_code:
            return True, "检测到跨目标色块写回"
    
    return False, None
```

**阻断处理**：
- 返回 `CROSS_TARGET_WRITEBACK` 错误
- 阻止写回操作
- 提示用户拆分任务

---

## RR-14: 修订理由强制

**规则**：所有修订必须包含 `revision_reason`。

**理由类型**：
- 基于新证据
- 修正错误
- 标准更新
- 用户反馈验证通过

**理由格式**：
```json
{
  "revision_reason": "基于新的责任人汇报（周报-2026-W23），目标已达成",
  "reason_type": "new_evidence",
  "evidence_ref": ["ev_001", "ev_002"]
}
```

---

## RR-15: 置信度更新

**规则**：修订后必须更新 `confidence_after_revision`。

**更新逻辑**：
```python
def update_confidence(revision_output, evidence_bundle):
    # 基于证据强度
    evidence_strength = calculate_evidence_strength(evidence_bundle)
    
    # 基于一致性检查
    consistency_bonus = 1.0 if revision_output.consistency_check.passed else 0.8
    
    # 基于风险标志
    risk_penalty = 0.7 if revision_output.review_flag else 1.0
    
    new_confidence = evidence_strength * consistency_bonus * risk_penalty
    revision_output.confidence_after_revision = min(new_confidence, 1.0)
```
