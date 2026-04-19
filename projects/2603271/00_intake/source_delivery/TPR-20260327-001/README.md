# TPR-20260327-001：bp-reporting-templates 复刻项目

**状态**：✅ 已完成
**目标**：将现有 bp-reporting-templates Skill 复刻为完整的交付包，供 Skill 工厂重新制造

---

## 项目结构

```
TPR-20260327-001/
├── README.md                    # 本文件（项目索引）
├── 01-discovery/
│   └── DISCOVERY.md            # 需求规格说明书
├── IMPLEMENTATION_PLAN.md     # 完整实现方案
├── code-skeleton/
│   ├── scripts/
│   │   ├── main.py           # 主入口
│   │   ├── input_handler.py  # 输入解析
│   │   ├── api_client.py    # API 调用
│   │   ├── parser.py        # BP 解析
│   │   ├── template_manager.py  # 模板管理
│   │   ├── filler.py        # 模板填充
│   │   ├── reviewer.py      # 审查器
│   │   └── utils.py         # 工具函数
│   ├── tests/
│   │   └── test_all.py     # 测试用例
│   └── requirements.txt    # Python 依赖
└── references/
    ├── 基础模板_月报.md
    ├── 基础模板_季报.md
    ├── 基础模板_半年报.md
    ├── 基础模板_年报.md
    ├── 通用填写规范.md
    ├── BP编码速查表.md
    └── alert_rules.yaml        # 颜色预警规则
```

---

## 核心功能

### 输入
- 组织名 / 个人名（从用户指令识别）
- BP 数据（从 API 获取或用户提供文件）
- 生成类型（"四套" / "季报" / "月报和年报" 等）

### 输出
- 月报填写规范（Markdown）
- 季报填写规范（Markdown）
- 半年报填写规范（Markdown）
- 年报填写规范（Markdown）

---

## API 配置

- Base URL: `https://sg-al-cwork-web.mediportal.com.cn/open-api`
- appKey: `TsFhRR7OywNULeHPqudePf85STc4EpHI`
- periodId: `1994002024299085826`（2026年度计划BP）

---

## 颜色预警规则

| 指标类型 | 🔴 红 | 🟡 黄 | 🟢 绿 |
|---------|------|------|------|
| 财务类 | >5% | 3-5% | <3% |
| 得分类 | >10% | 5-10% | <5% |
| 节点类 | delay>2周 | delay 1-2周 | 正常 |

**零容忍项**（任何偏离即红）：
- 重大合规事故
- BP签约率<100%
- 奖金发放delay

---

## 使用方式

### 命令行
```bash
cd code-skeleton/scripts
python main.py "为产品中心生成四套"
```

### Python API
```python
from main import generate_templates
import asyncio

result = asyncio.run(generate_templates("为林刚做季报"))
print(result)
```

---

## 交付清单

- [x] 需求规格说明书（DISCOVERY.md）
- [x] 完整实现方案（IMPLEMENTATION_PLAN.md）
- [x] 代码骨架（6个模块）
- [x] 参考文件（6个模板 + 1个配置）
- [x] 测试用例
- [x] 依赖声明（requirements.txt）

---

## 下一步

将此交付包发送给 Skill 工厂，按照 IMPLEMENTATION_PLAN.md 中的设计实现完整 Skill。
