# CMS 康哲药业投前评估报告样式文件 V1.0

> 用途：供 AI 将 CMS 投前评估报告 Markdown 转换为咨询风格的正式评估报告 HTML。
> 基于：风格 03（BD报告）架构扩展，新增 CMS 专属组件。

---

## 1. 整体风格定位

- 风格关键词：专业、审慎、投委会决策、Gate门控、对抗审查、咨询报告感
- 主色调：麦肯锡深蓝（#1a3a5c）为默认，可选投资蓝/酒红/森林青
- 视觉基调：沉稳、权威、层次分明，Gate 结论卡为核心视觉元素
- 页面适合导出为 PDF，A4 纵向
- 与风格 03 的关系：共享基础排版规范，但组件体系完全不同

---

## 2. CMS 报告标准章节结构

```
封面
目录
第一章：执行摘要
第二章：标的发现（DISCOVERY）
第三章：One-pager 终局先立
第四章：Gate 1 前提门
第五章：Gate 2 定调门
第六章：Gate 3 证据门
第七章：Gate 4 支付门
第八章：Gate 5 成本门
第九章：Gate 6 可做门
第十章：Gate Battle 对抗审查总结
综合评估结论
附录
参考文献
```

---

## 3. CMS 专属组件使用说明

### 3.1 Gate 结论卡

每个 Gate 章节末尾必须包含一个 Gate 结论卡。

**HTML 结构**：
```html
<div class="gate-card gate-conditional">
  <div class="gate-title">Gate 1 — 前提门 结论卡</div>
  <div class="gate-body">
    <p><span class="gate-label">结论</span> 有条件通过</p>
    <p><span class="gate-label">置信度</span> 低</p>
    <p>主要支撑依据：</p>
    <ul>
      <li>依据一</li>
      <li>依据二</li>
    </ul>
    <p>需补证据 Top 5：</p>
    <ol>
      <li>证据一</li>
      <li>证据二</li>
    </ol>
    <p>红旗事项：</p>
    <ul>
      <li>⚠️ 红旗一</li>
    </ul>
    <p>当轮处理决定：推进至 Gate 2</p>
  </div>
</div>
```

**状态选择**：
- `gate-pass`：通过（绿色） — 所有条件满足
- `gate-conditional`：有条件通过（琥珀色） — 需要补充证据
- `gate-stop`：停止（红色） — 触发否决条件

### 3.2 置信度徽章

在正文中引用数据时，标注置信度等级。

**HTML**：
```html
<span class="confidence-badge conf-a">A级</span> 高置信度
<span class="confidence-badge conf-b">B级</span> 中等置信度
<span class="confidence-badge conf-c">C级-待验证</span> 待验证
<span class="confidence-badge conf-d">D级-基于假设</span> 基于假设
```

**使用场景**：表格中数据来源标注、正文关键判断后缀。

### 3.3 Battle 对抗审查

双层审查结构，审查层先提出异议，执行层逐条回应。

**HTML**：
```html
<div class="battle-auditor">
  <span class="battle-label">审查层异议</span>
  <p><strong>异议 N：标题</strong></p>
  <p>异议内容...</p>
  <p>建议：...</p>
</div>
<div class="battle-executor">
  <span class="battle-label">执行层回应</span>
  <p>接受/部分接受/拒绝。原因...</p>
  <p>修改内容：...</p>
</div>
```

**争议点高亮**：
```html
<div class="battle-dispute">
  <strong>争议点：标题</strong><br>
  争议描述...
</div>
```

### 3.4 一票否决框

标记一票否决检查项。

**HTML**：
```html
<div class="veto-box">
  <strong>❌ 一票否决：注册路径完全封闭</strong><br>
  说明...
</div>
```

### 3.5 信息冲突框

标记审查中发现的数据矛盾。

**HTML**：
```html
<div class="conflict-box">
  <strong>⚠️ 信息冲突</strong><br>
  来源 A 声称 X，来源 B 声称 Y...
</div>
```

### 3.6 阶段标签

标记评估所处阶段。

**HTML**：
```html
<span class="stage-tag stage-a">阶段A</span>
<span class="stage-tag stage-b">阶段B</span>
```

### 3.7 DRL 优先级

标记待补证据的优先级。

**HTML**：
```html
<span class="drl-priority drl-p0">P0</span> 最高优先级
<span class="drl-priority drl-p1">P1</span> 中优先级
<span class="drl-priority drl-p2">P2</span> 低优先级
```

### 3.8 风险等级

标记供应链/竞争/注册等风险等级。

**HTML**：
```html
<div class="risk-high">高风险：说明...</div>
<div class="risk-medium">中风险：说明...</div>
<div class="risk-low">低风险：说明...</div>
```

### 3.9 中立审查框

第三方中立审查意见。

**HTML**：
```html
<div class="neutral-review">
  <strong>中立审查意见</strong><br>
  内容...
</div>
```

### 3.10 Gate 汇总表

综合评估章节使用汇总表，展示所有 Gate 结论。

**HTML**：
```html
<table class="gate-summary">
  <tr><th>Gate</th><th>结论</th><th>置信度</th></tr>
  <tr><td>Gate 1 前提门</td><td class="cond">有条件通过</td><td><span class="confidence-badge conf-c">C级</span></td></tr>
  <tr><td>Gate 2 定调门</td><td class="fail">未达标</td><td><span class="confidence-badge conf-d">D级</span></td></tr>
</table>
```

---

## 4. Do's and Don'ts

**Do：**
- 每个 Gate 章节后必须包含 Gate 结论卡
- 置信度标注使用标准四档徽章
- Battle 审查使用审查层+执行层双层结构
- 一票否决项使用 `.veto-box`（非 blockquote）
- 综合评估使用 Gate 汇总表
- 所有颜色通过 Token 配置，不硬编码

**Don't：**
- 不要用 blockquote 替代 Gate 结论卡
- 不要跳过 Battle 审查章节
- 不要在结论卡中混用不同状态色
- 不要使用状态色做装饰（仅用于语义标记）
- 不要使用 TailwindCSS 或动画
