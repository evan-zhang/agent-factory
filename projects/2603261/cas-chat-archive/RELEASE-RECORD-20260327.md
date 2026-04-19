# RELEASE-RECORD-20260327

项目：AF-20260326-002 / cas-chat-archive  
版本：v1.1.0-rc1

## 1) 发布结果

### ClawHub（公共）
- 状态：✅ 成功
- 版本：`cas-chat-archive v1.1.0-rc1`

### Internal Market（企业内部）
- 状态：✅ 成功
- 执行工具：`create-xgjk-skill`（一站式发布脚本）
- 注册结果：
  - `id`: `2037406010213437442`
  - `code`: `cas-chat-archive`
  - `name`: `CAS Chat Archive`
  - `isInternal`: `true`
  - `version`: `1.0`
  - `downloadUrl`: `https://filegpt-hn.file.mediportal.com.cn/skills/cas-chat-archive/1774590418-cas-chat-archive.zip`

## 2) 验证证据

- 详情查询：`python3 05_products/create-xgjk-skill/scripts/skill-management/get_skills.py --detail cas-chat-archive`
- 结果：可查到上述 `id/code/name/downloadUrl`，类型=内部。

## 3) 流程集成

- 已将“企业内部发布执行工具”纳入工厂全流程：
  - S6 企业发布默认执行路径：`create-xgjk-skill/scripts/skill-management/publish_skill.py`
- 已更新：SOP / IDX / Registry / 收口文档口径。

## 4) 页面核验闭环

- 已按规则引导访问：`https://skills.mediportal.com.cn/`
- 用户确认：已同意（核验闭环完成）
