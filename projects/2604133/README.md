# AF-20260413-003 — LLM Wiki 个人知识管理体系

## 定位
基于 Karpathy LLM Wiki 模式的个人知识管理体系。
参考：https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f

## 三层架构
1. **Raw sources**（原始文档）— 不可变，只读
2. **Wiki**（知识库）— LLM 生成和维护的 Markdown 文件，相互关联
3. **Schema**（规则文档）— 告诉 LLM 怎么组织 wiki

## 三个核心操作
- **Ingest**（入库）— 新内容进来，自动更新 wiki 里所有相关页面
- **Query**（查询）— 好的回答写回 wiki，知识不消失在聊天记录里
- **Lint**（检查）— 定期检查矛盾、过时信息、孤立页面

## 关键设计点
- index.md（内容索引）+ log.md（时间日志）双文件
- 每次入库更新所有相关页面，不只插一条记录
- 查询结果可回写 wiki，知识持续复利增长
- 支持 Obsidian graph view 可视化

## 状态
- 设计阶段，待专项讨论开发
- 已保存 Karpathy 原文 gist 供参考

## 关联项目
- AF-20260413-001（Link Archivist）：内容生产方
- AF-20260413-002（知识库同步）：本地-云端同步
- 本项目：知识组织与管理
