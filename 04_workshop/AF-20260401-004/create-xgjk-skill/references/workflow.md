# 创建 Skill 5步流程

> 完整操作手册：`docs/SKILL_CREATION_WORKFLOW.md`
> 协议规范：`docs/XGJK_SKILL_PROTOCOL.md`
> 验证清单：`docs/SKILL_VALIDATION_CHECKLIST.md`

## 流程总览

```
Step 1  意图理解与需求确认
        → 了解场景、获取文档、筛选API、精简字段

Step 2  按协议逐步生成
        → 搭骨架、写固定文件、生成SKILL.md
        → 逐个API生成（文档+脚本+场景，一个完成再下一个）
        → 写索引

Step 3  三轮反思检查
        → 验证清单A-H → 交叉验证（附证据）→ 与示例结构比对

Step 4  最终确认
        → 确认所有修复项清零

Step 5  完成输出总结
```

## 关键约束

- **顺序执行**：Step 1→2→3→4→5，不可跳步
- **每步确认**：每步完成后需用户确认才进入下一步
- **三个固定文件**：`common/auth.md`、`common/conventions.md`、`openapi/common/appkey.md` 从协议附录原样复制，一字不改
- **逐个API生成**：Step 2.3 必须一个API写完全套再进下一个
- **Step 3不可跳过**：三轮反思检查是质量门控，必须完整执行
- **生产域名**：生成前确认生产域名，未提供用 `{待确认域名}` 占位

## 发现→创建→发布 完整链路

```bash
# 发现（无需token）
python3 scripts/skill-management/get_skills.py

# 发布（需要XG_USER_TOKEN）
python3 scripts/skill-management/publish_skill.py ./my-skill --code my-skill --name "我的Skill"

# 更新
python3 scripts/skill-management/publish_skill.py ./my-skill --code my-skill --update --version 2

# 下架
python3 scripts/skill-management/delete_skill.py --id <skill-id>
```
