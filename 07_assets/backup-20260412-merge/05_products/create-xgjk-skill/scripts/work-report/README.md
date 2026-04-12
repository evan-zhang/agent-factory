# work-report 脚本

## send_report_with_confirm.py

发送工作汇报的两阶段脚本：

1. `prepare` 生成发送前确认单（JSON），并解析建议人/决策人
2. `send` 在人工确认后发送（会把建议人/决策人写入 `reportLevelList`）

### 成功发送关键实践（已验证）
- 附件先调：`POST /open-api/cwork-file/uploadWholeFile`
- 汇报提交时：`fileVOList` 仅传 `fileId + name + type=file`
- 服务器繁忙（`resultCode=200000`）时做有限重试（2秒间隔）

### 用法

```bash
python3 send_report_with_confirm.py prepare \
  --title "玄关健康BP 月度及季度各部门填报模板" \
  --content "附件压缩包内为各部门按月及按季..." \
  --to "张成鹏,侯桐" \
  --to-groups "AI研究小组" \
  --cc "屈军利,李广智,成伟" \
  --advisors "成伟" \
  --approvers "侯桐,屈军利" \
  --attachments "./UAT-附件清单-20260327.txt,./CWORK-UAT-Report-20260327.md,./AF-20260327-001-UAT-Bundle-20260327.zip" \
  --out ./report-confirmation.json

python3 send_report_with_confirm.py send \
  --confirm-json ./report-confirmation.json \
  --confirm-token CONFIRM_SEND
```

### 联系人分组管理

```bash
python3 group_contacts.py list
python3 group_contacts.py create --name "项目核心组"
python3 group_contacts.py rename --group "项目核心组" --new-name "项目核心组-2026"
python3 group_contacts.py members --group "项目核心组-2026" --add "成伟,侯桐" --remove "李广智"
```

### 环境变量
- `BP_APP_KEY` 或 `COMPANY_APP_KEY`
