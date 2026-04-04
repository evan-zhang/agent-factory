# 意图路由表

## 🔍 发现 Skill

| 用户说 | 脚本 | 需要 token |
|---|---|---|
| "打开技能管理"/"打开玄关Skill" | `open https://skills.mediportal.com.cn` | 否 |
| "有哪些Skill"/"查看列表" | `scripts/skill-management/get_skills.py` | 否 |
| "搜索 xxx Skill" | `get_skills.py --search xxx` | 否 |
| "看看 xxx 的详情" | `get_skills.py --detail xxx` | 否 |

## 🛠️ 创建 Skill

| 用户说 | 路由 | 需要 token |
|---|---|---|
| "构建Skill包"/"按模板创建Skill" | 5步流程（见 workflow.md）| 否 |
| "获取接口文档"/"拉取API定义" | `scripts/fetch_api_doc.py` | 否 |

## 🚀 发布 Skill

| 用户说 | 脚本 | 需要 token |
|---|---|---|
| "帮我发布这个Skill" | `publish_skill.py` | 是 |
| "更新这个Skill" | `publish_skill.py --update` | 是 |
| "打包Skill"/"生成ZIP" | `pack_skill.py` | 否 |
| "上传到七牛" | `upload_to_qiniu.py` | 是 |
| "注册Skill" | `register_skill.py` | 是 |
| "更新Skill信息" | `update_skill.py` | 是 |
| "下架Skill"/"删除Skill" | `delete_skill.py` | 是 |

## 📨 工作汇报

| 用户说 | 脚本 |
|---|---|
| "发工作汇报"/"先给我确认再发" | `work-report/send_report_with_confirm.py prepare` |
| "确认发送" | `work-report/send_report_with_confirm.py send` |
| "查看联系人分组" | `work-report/group_contacts.py` |

**汇报约束**：发送前必须展示确认单（标题/正文/接收人/抄送人/附件），获得明确"确认发送"才执行。姓名必须解析到唯一员工，模糊命中先回显候选。
