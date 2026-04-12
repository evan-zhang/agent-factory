# skill-management 模块接口索引

> Skill 生命周期管理：打包、上传、注册、更新、下架、查询

| 接口 | 方法 | 说明 | 需要鉴权 | 文档 | 脚本 |
|---|---|---|---|---|---|
| **publish-skill** | **组合** | **一站式发布：打包→上传→注册/更新** | **是** | [publish-skill.md](./publish-skill.md) | [publish_skill.py](../../scripts/skill-management/publish_skill.py) |
| pack-skill | 本地 | 打包 Skill 目录为 ZIP | 否 | [pack-skill.md](./pack-skill.md) | [pack_skill.py](../../scripts/skill-management/pack_skill.py) |
| upload-to-qiniu | GET+POST | 获取七牛凭证 + 上传文件 | 是 | [upload-to-qiniu.md](./upload-to-qiniu.md) | [upload_to_qiniu.py](../../scripts/skill-management/upload_to_qiniu.py) |
| register-skill | POST | 注册（发布）新 Skill | 是 | [register-skill.md](./register-skill.md) | [register_skill.py](../../scripts/skill-management/register_skill.py) |
| update-skill | POST | 更新已有 Skill | 是 | [update-skill.md](./update-skill.md) | [update_skill.py](../../scripts/skill-management/update_skill.py) |
| delete-skill | POST | 下架（删除）Skill | 是 | [delete-skill.md](./delete-skill.md) | [delete_skill.py](../../scripts/skill-management/delete_skill.py) |
| get-skills | GET | 获取已发布 Skill 列表 | 否 | [get-skills.md](./get-skills.md) | [get_skills.py](../../scripts/skill-management/get_skills.py) |
