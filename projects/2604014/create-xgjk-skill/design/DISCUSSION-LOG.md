# DISCUSSION LOG - create-xgjk-skill

## 2026-03-27 22:08
- 触发背景：Evan 要求把“这次成功发送经验”固化到 SeaWork/CWork 流程。
- 用户反馈/诉求：
  - 强化姓名识别与判断细节；
  - 发送前确认页必须完整；
  - 附件经常失败，需把成功方法写死。
- 关键决策：
  - 采用两阶段发送：`prepare`（确认单）→ `send`（确认后发送）；
  - 未确认/未解析/附件缺失一律阻断发送；
  - 附件固定走 uploadWholeFile + fileId 提交。
- 需要修改的内容：
  - 新增 `scripts/work-report/send_report_with_confirm.py`；
  - 新增 `scripts/work-report/README.md`；
  - 更新 `SKILL.md` 路由与约束。
- 执行结果：完成改造并可生成确认单；姓名纠偏规则已加入。
- 待办：补充 post-send 出箱核验能力。

## 2026-03-27 22:26
- 触发背景：Evan 询问 CWorker API 是否升级、是否可扩展新功能。
- 用户反馈/诉求：确认新 API 面与能力扩展方向，提升 SeaWork skill 能力。
- 关键决策：
  - 识别 03-work-report/04-cwork-file/05-cwork-user 三组可用能力；
  - 采用 P0/P1/P2 分层扩展路线。
- 需要修改的内容：
  - P1 增加 inbox/outbox 核验、未读看板、reply；
  - P2 增加 template/todo/AI 问答能力。
- 执行结果：完成 API 面盘点，确认当前可扩展并给出路线。
- 待办：按 P1 排期落实现网脚本与文档。

## 2026-03-28 08:20~09:00 (Asia/Shanghai)
- 触发背景：CWork 联系人分组接口接入与 --to-groups 参数实现。
- 关键决策：
  - 新增 group_contacts.py（list/create/rename/members 四个命令）
  - send_report_with_confirm.py 新增 --to-groups 参数，按分组名解析成员展开去重进入 acceptEmpIdList
  - 未解析分组阻断发送
- 执行结果：已创建6个个人联系人分组（工作协同开发组/知识库小组/AI能力小组/BP开发组/TBS训战小组/SFE小组）
- SFE小组固定角色映射确认：王馗=接收人+建议人；侯桐=决策人；成伟/屈军利=抄送人
