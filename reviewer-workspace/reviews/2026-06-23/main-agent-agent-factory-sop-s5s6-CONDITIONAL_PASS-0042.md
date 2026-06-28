## 审查结论

**总体评级**：CONDITIONAL_PASS  
**置信度**：0.82  
**审查对象**：A 类业务评审 — agent-factory-sop S5/S6 发布流程简化方案  
**审查时间**：2026-06-23 00:42 GMT+8  
**使用模型**：gsykj-anthropic/claude-sonnet-4-6

---

**维度评分**

| 维度 | 评分（1-5） | 简评 |
|------|------------|------|
| 必要性 | 4 | 删除 builds/releases zip 与当前实际 GitHub 分发链路一致，能降低流程摩擦；但 zip 原本承担离线快照/不可变包能力，需用 git tag 或 release 替代。 |
| 充分性 | 4 | GitHub-only 对当前个人/实例级 Skill 分发足够，README 已采用 git clone 安装；但私有仓库、网络不可达、企业内部市场等场景需明确例外路径。 |
| 风险 | 3 | 最大风险是“发布=push HEAD”导致版本、回滚、验收边界不清；必须补 tag、commit hash、回滚命令和安装说明锁定策略。 |
| 一致性 | 3 | 主 SKILL.md 当前 S5 没有 builds 步骤、S6 仍有 releases zip；参考规范仍写 S5 builds/S6 releases，且 S8 归档需要记录发布证据。 |
| 遗漏 | 3 | 遗漏 GitHub 仓库权限/可见性、tag/release 策略、安装前已存在目录处理、更新/回滚命令、S7 验收证据。 |

---

**问题清单**

| ID | 严重度 | 类别 | 位置 | 描述 | 证据 | 建议 |
|----|--------|------|------|------|------|------|
| F001 | major | 版本与回滚 | 改动方案 S6 | “git push 到 GitHub”作为唯一发布动作不足以形成可回滚、可引用的发布点；如果用户直接 clone 默认分支，回滚只能依赖人工找历史 commit。 | 现有 SOP 要求版本写入 VERSION 或正文版本记录（SKILL.md:12、158-159），S6 当前也在发布前后处理 VERSION/git push（SKILL.md:191-199）；参考规范原本通过 `releases/v{版本号}-timestamp.zip` 形成版本化产物（AF-SOP v5.4:317-327）。 | 删除 zip 可以接受，但 S6 必须新增：发布前确认 VERSION semver；创建并 push `vX.Y.Z` tag；安装说明同时给默认 clone 和锁定版本命令（如 `git checkout vX.Y.Z`）；回滚说明给 `git fetch --tags && git checkout v旧版本`。 |
| F002 | major | 分发充分性 | 改动方案“GitHub 是唯一分发渠道” | GitHub-only 符合当前三个案例，但不能无条件替代所有发布渠道，尤其是私有仓库权限、网络受限、内部市场/企业发布等场景。 | README 已给出 GitHub clone 安装方式（README:24-30），说明当前仓库确实以 GitHub 分发；但治理规范中仍存在 ClawHub/内部市场双发布链路与兼容性要求（SRS-XGJK:26-33、151-183）。 | 在 SOP 中定义适用范围：“默认个人/当前 Gateway Skill 使用 GitHub-only；若目标用户无法访问 GitHub、需要企业市场/ClawHub、或需要离线交付，则走例外发布路径/另行方案”。不要把 GitHub-only 写成全域唯一真理。 |
| F003 | major | SOP 一致性 | SKILL.md 与 references | 主 SKILL.md 的 S5 已没有 builds 打包，但完整规范 references 仍要求 S5 构建测试包、S6 releases 打包；如果只改主文档，引用的完整规范会继续误导执行方。 | 主 SKILL.md S5 仅包含自动检查、风险自检、测试计划、C 类评审（SKILL.md:153-189）；参考规范仍写 S5 `../builds` zip（AF-SOP v5.4:236-248）与 S6 `../releases` zip（AF-SOP v5.4:317-327）；主 SKILL.md 完整规范引用仍指向该文件（SKILL.md:265）。 | 同步更新或标注废弃 references 中的 S5/S6 打包段；至少在主 SKILL.md 加“若与 references 冲突，以本 SKILL.md S5/S6 为准”，并在 S8 归档记录本次决策。 |
| F004 | major | 验收边界 | S7/S8 | 不区分测试分发和正式发布可以简化，但必须保留“已验证版本”的边界；否则 S7 用户验收对象可能是不断变化的 main 分支。 | SOP 要求每步用户确认（SKILL.md:35），S5 用户本地测试后才 C 类评审（SKILL.md:179-189），S7 又做最终验收（SKILL.md:201-213）。 | 在 S5 测试时记录被测 commit；S6 发布时 tag 同一 commit；S7 验收报告引用 repo URL、commit hash/tag、安装路径和测试结果，避免验收对象漂移。 |
| F005 | minor | 安装说明完整性 | 安装说明标准格式 | 给出的标准格式只有首次 clone，不覆盖已存在目录、更新到新版、切换指定版本、私有仓库鉴权失败等常见情况。 | 当前 README 安装示例同样只有 `git clone ... ~/.openclaw/skills/agent-factory-sop`（README:24-30）。 | 标准安装说明增加四块：首次安装、更新、锁定版本/回滚、验证命令/测试方向；私有 repo 增加“需 GitHub 权限/SSH 或 token 配置”提示。 |
| F006 | minor | 归档与证据 | S8 | 删除 zip 后，发布证据从“文件产物”变为“远端仓库状态”，S8 的归档内容需随之调整。 | S8 当前只要求更新设计档案、经验教训、迭代方向（SKILL.md:215-220），没有明确记录发布 URL/tag/commit。 | S8 增加发布记录字段：repo URL、tag、commit hash、VERSION、安装说明快照、S5/S7 测试摘要。 |

---

**五项评审维度结论**

1. **必要性**：方案方向成立。builds/release zip 在当前 GitHub clone 实践中是重复产物，且主 SKILL.md 的 S5 已不再实际构建测试包。删除它们能减少执行成本和“文档说一套、实际做一套”的偏差。但 zip 提供的“不可变快照”能力不能直接丢弃，需要用 git tag/commit hash 替代。
2. **充分性**：对当前个人 OpenClaw/Gateway skills 分发足够；README 的安装方式也证明 GitHub clone 是现行渠道。但对私有仓库、受限网络、企业内部市场、离线交付不充分，SOP 需把这些定义为例外路径。
3. **风险**：主要风险不是没有 zip，而是没有稳定发布标识。若只有 push main，则测试、发布、验收会指向不同 HEAD。最低补强是“VERSION + commit hash + tag + 安装说明 + 回滚命令”。
4. **一致性**：需同步清理 references/完整规范，否则执行者可能继续按旧文档构建 builds/releases。S5/S6/S7/S8 的证据链也要改为 Git 证据链。
5. **遗漏**：缺少 tag 策略、回滚策略、私有仓库权限提示、已安装目录处理、S8 发布证据归档、与内部市场/ClawHub 的边界声明。

---

**建议改法（可直接落入 SOP）**

- **S5 质量验证**：保持 Validator 自动检查、风险自检、用户本地安装到当前 Gateway skills 目录测试、C 类评审；记录被测 `commit hash`。删除 builds zip。
- **S6 发布**：更新 VERSION → git commit → 创建 `v{VERSION}` tag → push commit 和 tag 到 GitHub → 生成安装说明。删除 releases zip。
- **安装说明标准格式**建议改为：

```md
📦 {skill-name} v{版本号}

仓库：https://github.com/evan-zhang/{repo}
发布版本：v{版本号}
Commit：{commit-hash}

首次安装：
git clone https://github.com/evan-zhang/{repo}.git ~/.openclaw/skills/{skill-name}
cd ~/.openclaw/skills/{skill-name} && git checkout v{版本号}

更新到本版：
cd ~/.openclaw/skills/{skill-name} && git fetch --tags && git checkout v{版本号}

回滚：
cd ~/.openclaw/skills/{skill-name} && git fetch --tags && git checkout v{上一稳定版本}

变更摘要：...
测试方向：...
权限提示：私有仓库需先确保目标环境具备 GitHub 访问权限。
```

- **S7/S8**：验收与归档引用 tag/commit，而不是 zip 文件；S8 保存安装说明快照和测试摘要。
- **例外路径**：若用户要求离线交付、GitHub 不可达、企业市场发布、或对外正式发行需要资产包，则另走“例外发布流程”（可用 GitHub Release/zip artifact/内部市场），不作为默认路径。

---

**最重要的一条建议**

可以删除 builds/releases zip，但必须把“zip 产物的版本快照能力”替换为 **VERSION + git tag + commit hash + 回滚说明 + S8 归档证据**，否则发布和验收会失去稳定锚点。
