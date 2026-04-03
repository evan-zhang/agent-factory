# RULES.md — 造物 (factory-orchestrator) 核心规则索引

> 本文件是机器可读的快速查阅索引。每次涉及模型配置、协作规则、人员信息、项目台账时，**先读本文件**，不靠语义搜索。
> 最后更新：2026-03-28

---

## 一、协作行为规则（最高优先级）

0. **必须用中文回复**：所有面向用户的消息一律中文，禁止英文回复。内部推理也尽量用中文。违反此规则等于违反最高优先级。
1. **默认只讨论，不执行**：除非 Evan 明确说"确认执行"，否则不做任何写/发/改/重启动作。
2. **执行前必须先给执行前清单（GRV-Lite V3 格式）**，Evan 确认后才动手。
3. **预计 >2 分钟任务，默认走子 Agent**，主会话不被阻塞。
4. **没有记录=没有发生**（铁律）：每次执行必须有文档留痕。
5. 外发/改配置/重启 属于**高风险动作**，必须在执行前清单里显式声明，并二次确认。
6. 改自己 Agent 配置可以自己做；改 gateway 全局配置/其他 Agent 配置必须交给 ops agent。

---

## 二、执行前清单格式（GRV-Lite V3，固定顺序）

```
G 目标
R 关键成果（2-4条，可验收）
V 关键举措（3-6步）
预计时长（总时长+分项）
执行方式（直执 / 子Agent / 混合）
执行人+模型
影响范围
风险与回滚
输出与成功判据
确认口令（用户回复"确认执行"才动手）
```

---

## 三、模型配置（已生效，2026-03-28）

### factory-orchestrator 主 Agent
| 类型 | 模型 |
|---|---|
| 主模型 | `custom-claude-company/claude-sonnet-4-6` |
| 备选1 | `openai-codex/gpt-5.3-codex` |
| 备选2 | `zai/glm-5` |
| 备选3 | `custom-openai-company/glm-5_codingplan` |
| 备选4 | `custom-openai-company/glm-5` |

配置位置：`~/.openclaw/gateways/life/openclaw.json` → `agents.list[id=factory-orchestrator].model`

### 子 Agent（sessions_spawn 时显式指定）
| 类型 | 模型 |
|---|---|
| 主模型 | `openai-codex/gpt-5.3-codex` |
| 备选1 | `zai/glm-5` |
| 备选2 | `custom-openai-company/glm-5_codingplan` |
| 备选3 | `custom-openai-company/glm-5` |

> 子 Agent 模型通过 `sessions_spawn(model=...)` 参数指定，不依赖 gateway 全局默认。

参考标准：TPR 三省工作法模型配置（Evan 2026-03-28）

---

## 四、关键人员 empId（CWork）

| 姓名 | empId | 常见误写 |
|---|---|---|
| 张成鹏（Evan） | `1514822105176903682` | — |
| 侯桐 | `1514822114043662337` | 侯彤、侯通 |
| 屈军利 | `1514822127830339585` | 屈俊丽 |
| 李广智 | `1514822107563462658` | — |
| 成伟 | `1514822118611259394` | 陈伟 |
| 王馗 | `1514822180686958594` | — |
| 蹇晓枫 | `1514822100860964865` | 简小凤 |
| 付光伟 | `1514822093512544258` | — |
| 刘艳华 | `1514822134612529153` | — |
| 欧倩 | `1514822133731725314` | — |
| 宋培众 | `1514822080577310721` | — |
| 黄巍 | `2008004387209052161` | — |
| 曾文哲 | `1920299536813834241` | — |
| 罗毓娴 | `1514822109652226050` | 罗玉贤 |
| 封敏 | `1514822174454222850` | — |
| 杨晶晶 | `1514822190413549570` | — |

---

## 五、CWork 联系人分组

| 分组名 | groupId | 成员 |
|---|---|---|
| AI研究小组 | `1772511589912629249` | 侯桐/宋培众/李广智/杨晶晶/于耀 |
| 常用联系人 | `1823990988488704001` | 成伟/覃晓庆/薛芳芳/刘丽华 |
| 工作协同开发组 | `2037687429049110529` | 成伟/蹇晓枫/付光伟/屈军利/侯桐 |
| 知识库小组 | `2037688322872320001` | 成伟/侯桐/屈军利/刘艳华/欧倩 |
| AI能力小组 | `2037688968908382210` | 李广智/成伟/屈军利/侯桐/宋培众/黄巍 |
| BP开发组 | `2037690718872674305` | 封敏/杨晶晶/侯桐/成伟/屈军利/曾文哲 |
| TBS训战小组 | `2037691070556676098` | 罗毓娴/李广智/付光伟/侯桐/屈军利 |
| SFE小组 | `2037691449692147714` | 王馗/侯桐/成伟/屈军利 |

### SFE小组固定角色映射
| 人员 | 角色 |
|---|---|
| 王馗 | 接收人（To）+ 建议人（suggest） |
| 侯桐 | 决策人（decide） |
| 成伟 | 接收人（To）+ 建议人（suggest） |
| 屈军利 | 抄送人（CC）+ 决策人（decide） |

---

## 六、CWork 外发规则（强制）

1. 任何外发必须先给"发送前确认单"，包含：标题/正文/接收人/抄送人/建议人/审批人/附件
2. 用户回复"确认发送"后才执行发送
3. 建议人写入 `type=suggest`，决策人写入 `type=decide`，均需姓名解析获得 empId
4. 未解析到 empId 的人员阻断发送（不允许空 empId 提交）
5. 发送成功后记录回执 ID 到对应项目台账

---

## 七、密钥规则

- 标准 appKey（测试用）：`TsFhRR7OywNULeHPqudePf85STc4EpHI`
- 环境变量：`BP_APP_KEY`（优先）/ `COMPANY_APP_KEY`（兼容）
- **禁止硬编码到 Skill 代码中**
- Skill 运行时由用户通过环境变量提供，测试时使用上述 key
- 已持久化到 `~/.zshrc` / `~/.zprofile` + `launchctl setenv`
- **API Base URL**：`https://sg-al-cwork-web.mediportal.com.cn/open-api`（注意：v1.4文档更新了域名，旧为 sg-cwork-api）
- **接口文档来源**：`https://github.com/xgjk/dev-guide`（见十四章节）；将来开发任何 CWork/玄关系产品 Skill，必须先拉取此仓库最新文档再动手

---

## 八、项目台账（活跃）

| 编号 | 名称 | 状态 | 关键路径 |
|---|---|---|---|
| AF-20260323-001 | CWork 工作协同 | S8 维护中 | `05_products/create-xgjk-skill/` |
| AF-20260326-002 | CAS 聊天归档系统 | S8 观察期 | `04_workshop/AF-20260326-002/` |
| AF-20260327-001 | bp-reporting-templates | READY_FOR_RELEASE | `04_workshop/AF-20260327-001/` |
| AF-20260328-002 | cms-sop 统一SOP框架 | RELEASED | `05_products/cms-sop/` |

完整台账：`03_governance/factory-registry.md`

---

## 九、SOP 体系

| SOP | 适用场景 | 状态 |
|---|---|---|
| AF-SOP-01 | Skill 从0到1开发（主流程） | 生效中，不可污染 |
| cms-sop（Lite模式）| 20分钟内/单系统/简单任务 | ✅ 已发布 v1.0.0 |
| cms-sop（Full模式）| 复杂/长链路/跨系统任务 | ✅ 已发布 v1.0.0 |

---

## 十、CAS 巡检规则

- 巡检范围：`life` / `ops` / `company`（三个 gateway）
- 豁免：`code`（服务停用，不计入异常）
- 关键挂载路径：`hooks.internal.entries.cas-chat-archive-auto`
- hook 源文件：`04_workshop/AF-20260326-002/cas-chat-archive/hooks/`
- 归档默认路径：`~/.openclaw/chat-archive/{gateway}/`

---

## 十一、内部发布规则

- 双通道发布：ClawHub + 公司内部 Skill 市场
- 内部市场主页（发布后必须引导核验）：`https://skills.mediportal.com.cn/`
- 密钥标准：统一使用 `TsFhRR7OywNULeHPqudePf85STc4EpHI`

---

*本文件由造物维护，每次规则变更必须同步更新此文件。*

---

## 十一、Skill 源码统一管理规则（2026-03-29）

### 所有 Skill 源码统一存放于工厂 `05_products/`

| Skill | 工厂路径 | 说明 |
|---|---|---|
| `cms-cwork` | `05_products/cms-cwork/` | 软链接到 workspace-life/skills/cms-cwork |
| `cas-chat-archive` | `04_workshop/AF-20260326-002/cas-chat-archive/` | 工厂 workshop |
| `bp-reporting-templates` | `04_workshop/AF-20260327-001/04_execution/workspace/bp-reporting-templates/` | 工厂 workshop |
| `cms-sop` | `05_products/cms-sop/` | 工厂 products（Lite+Full合并版）|
| `create-xgjk-skill` | `05_products/create-xgjk-skill/` | 工厂 products |
| `self-improving-proactive-agent` | `05_products/self-improving-proactive-agent/` | 工厂 products |

### 维护规则
- **修改任何 Skill** → 改工厂对应目录，不改其他位置
- **发布** → 从工厂目录直接 `clawhub publish`
- **cms-cwork 特殊说明**：工厂路径通过软链接同步到 `workspace-life/skills/cms-cwork/`，运行时透明
- `node_modules/dist/package-lock.json` 保留在 workspace-life 备份目录，通过软链接引用，不纳入版本控制


---

## 十二、CAS Hook 挂载状态（2026-03-29 核实）

**结论：已正常挂载，风险关闭。**

- life/ops/company 三个 gateway 均配置 `cas-chat-archive-auto`（`enabled: true`）
- `openclaw hooks list` 显示状态：`✓ ready`，来源：`openclaw-managed`
- managed hook 由插件系统自动发现，不需要手动配置 handler 路径
- code gateway 豁免（服务停用，Evan 已确认）

**历史误判**：曾认为 `"enabled": true` 不含路径=未生效，实际上 managed hook 机制下这是正常配置。

---

## 十三、Skill 渐进式加载设计三原则（2026-03-29 确认）

> 适用于工厂所有新建 Skill，存量 Skill 改版时同步改造。

### 原则一：SKILL.md 是路由层，硬上限 120行

- 只写：触发词、模式判断、强制加载指令、能力索引
- 禁止写：执行规则、使用示例、注意事项、字段说明
- 超过120行视为设计违规，必须拆分到子文档

### 原则二：执行规则按场景单一职责分文件，放 references/

- 每个 references/*.md 只讲一件事，职责不拆散
- 共享规则（状态机/确认协议/升级规则）放 references/shared/
- 读取是显式行为：SKILL.md 里必须有"执行前必须 read 对应子文档"的强制指令
- 每次触发必须重新读取，禁止依赖上一次的加载缓存
- 子文档第一行写 `# 已加载 xxx.md`，作为加载确认标记

### 原则三：轻任务直接执行，复杂任务 spawn 子 Agent

- Lite/简单路径：读 guide → 直接执行
- Full/复杂路径：读 guide → spawn 子 Agent（只注入当前任务需要的规则）→ 子 Agent 写文件 → 主 Agent 读文件获取结果
- 子 Agent 结果通过文件传递，禁止通过自由文本解析
- spawn 时模型优先用 `custom-claude-company/claude-sonnet-4-6`

### 存量 Skill 改造优先级

| Skill | 优先级 | 说明 |
|---|---|---|
| `cms-sop`（新建）| 内置 | 第一个按新架构设计的 Skill |
| `cms-cwork` | P1 | SKILL.md 过长（64+能力），下次改版时拆分 |
| `cms-sop` | 内置 | 渐进式加载原生支持，已发布 v1.0.0 |
| `bp-reporting-templates` | P2 | 双门禁规则复杂，值得拆 |
| `cas-chat-archive` | P3 | 单一场景，影响小 |


---

## 十四、关键资源地址（固定，不靠语义搜索）

| 资源 | 地址 | 说明 |
|---|---|---|
| 玄关开发平台 API 文档仓库 | `https://github.com/xgjk/dev-guide` | 工作协同/CWork 接口文档；**Agent 可直接 curl 访问**；Raw 文件前缀：`https://raw.githubusercontent.com/xgjk/dev-guide/main/` |
| CWork API Base URL | `https://sg-cwork-api.mediportal.com.cn` | 生产环境接口地址 |
| 内部 Skill 市场 | `https://skills.mediportal.com.cn/` | 企业内部发布验证地址 |

---

## 十五（补充）、草稿附件校验策略（2026-03-29 确认）

**策略：附件校验放在"查看草稿"时，自动补挂，不打扰用户。**

- `draftDetail` 读回草稿后，比对 `fileList` 数量与预期附件数量
- 如果不一致：**自动调 5.24 更新草稿**（全量覆盖，带完整 fileVOList），再读回验证
- 二次验证仍失败：报错告知用户，不继续流程
- 验证通过后：展示确认单（用户看到的已是修复后的真实状态）
- 不提示用户、不需要用户确认补挂动作
- fileId 可以复用（同一文件不需要重复上传）
