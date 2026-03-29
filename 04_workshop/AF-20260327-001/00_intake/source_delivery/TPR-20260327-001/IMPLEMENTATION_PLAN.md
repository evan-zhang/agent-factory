# IMPLEMENTATION_PLAN.md - bp-reporting-templates 复刻

**项目编号**：TPR-20260327-001
**版本**：v1.0
**状态**：草案

---

## 1. 项目概述

### 1.1 目标

将现有 bp-reporting-templates Skill 复刻为标准化交付包，包含：
- 需求规格说明书
- 设计方案
- 实现方案
- 代码骨架

### 1.2 输入输出

**输入**：
- 组织名 / 个人名（从用户指令识别）
- BP 数据（从 API 获取或用户提供文件）
- 生成类型（"四套" / "季报" / "月报和年报" 等）

**输出**：
- 月报填写规范（Markdown）
- 季报填写规范（Markdown）
- 半年报填写规范（Markdown）
- 年报填写规范（Markdown）

---

## 2. 功能设计

### 2.1 核心功能模块

```
┌─────────────────────────────────────────────────────────────┐
│                    bp-reporting-templates                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Input     │  │   Parser    │  │   Filler    │         │
│  │  Handler    │→ │   Engine    │→ │   Engine    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│         ↓                ↓                ↓                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Config    │  │   Template  │  │  Reviewer   │         │
│  │   Loader    │  │   Manager   │  │   Engine    │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 模块说明

| 模块 | 职责 |
|------|------|
| Input Handler | 解析用户指令，识别组织/个人名称、生成类型 |
| Parser Engine | 解析 BP 数据，提取编码、衡量标准、数字锚点 |
| Template Manager | 管理四种模板（月报/季报/半年报/年报） |
| Filler Engine | 将 BP 数据填充到模板 |
| Reviewer Engine | 审查填充结果，检查编码对齐、数字锚点等 |
| Config Loader | 加载配置文件（颜色预警规则、零容忍项等） |

### 2.3 数据流

```
用户指令 → Input Handler → [组织名/个人名, 生成类型]
                                ↓
                    调用 API 获取 BP 数据（可选）
                                ↓
                    Parser Engine → [BPGoal列表]
                                ↓
                    Template Manager → [目标模板]
                                ↓
                    Filler Engine → [填充后模板]
                                ↓
                    Reviewer Engine → [审查结果]
                                ↓
                    输出 Markdown 文件
```

---

## 3. API 集成

### 3.1 可用 API

基于玄关开发者平台（与 BP 系统共用）：

| API | 用途 | Path |
|-----|------|------|
| getTree | 获取组织架构树 | `/bp/group/getTree` |
| getSimpleTree | 获取 BP 树 | `/bp/task/v2/getSimpleTree` |
| getGoalAndKeyResult | 获取目标详情 | `/bp/task/v2/getGoalAndKeyResult` |

**API 配置**：
- Base URL: `https://sg-al-cwork-web.mediportal.com.cn/open-api`
- appKey: `TsFhRR7OywNULeHPqudePf85STc4EpHI`
- periodId: `1994002024299085826`（2026年度计划BP）

### 3.2 数据获取流程

```
1. 用户输入组织名/个人名
       ↓
2. 调用 getTree 获取组织架构
       ↓
3. 在树中匹配 groupId
       ↓
4. 调用 getSimpleTree 获取 BP 树
       ↓
5. 调用 getGoalAndKeyResult 获取每个目标的详情
       ↓
6. 输出结构化 BP 数据
```

---

## 4. 模板设计

### 4.1 四种模板的章节结构

所有模板统一为 **8 章**：

| 章节 | 月报 | 季报 | 半年报 | 年报 |
|------|------|------|--------|------|
| 1. 汇报综述 | ✓ | ✓ | ✓ | ✓ |
| 2. BP目标承接 | ✓ | ✓ | ✓ | ✓ |
| 3. 核心结果 | ✓ | ✓ | ✓ | ✓ |
| 4. 关键举措 | ✓ | ✓ | ✓ | ✓ |
| 5. 问题偏差 | ✓ | ✓ | ✓ | ✓ |
| 6. 风险预警 | ✓ | ✓ | ✓ | ✓ |
| 7. 下期安排 | ✓ | ✓ | ✓ | ✓ |
| 8. 需决策事项 | ✓ | ✓ | ✓ | ✓ |

### 4.2 填充规则

**第2章 BP目标承接**（核心章节）：

```markdown
### 2.{n} [{BP维度名称}]

**对标BP：** {P系列编码}（个人）/ {A系列编码}（组织）

**{时间维度}承接重点：**
- {引用BP原文的举措}

**当前状态：**
- 量化指标：{引用BP原文的数字锚点}
- 偏离判断：{红/黄/绿}

**是否偏离预期：**
- {是/否}，{偏离率}
```

### 4.3 颜色预警规则

```yaml
alert_rules:
  financial:
    red: ">5%"
    yellow: "3-5%"
    green: "<3%"
  
  score:
    red: ">10%"
    yellow: "5-10%"
    green: "<5%"
  
  milestone:
    red: "delay>2周"
    yellow: "delay 1-2周"
    green: "正常"

zero_tolerance:
  - "重大合规事故"
  - "BP签约率<100%"
  - "奖金发放delay"
```

---

## 5. 代码架构

### 5.1 目录结构

```
bp-reporting-templates/
├── SKILL.md
├── references/
│   ├── 基础模板_月报.md
│   ├── 基础模板_季报.md
│   ├── 基础模板_半年报.md
│   ├── 基础模板_年报.md
│   ├── 通用填写规范.md
│   ├── BP编码速查表.md
│   └── alert_rules.yaml
├── scripts/
│   ├── main.py              # 主入口
│   ├── input_handler.py     # 输入解析
│   ├── api_client.py        # API 调用
│   ├── parser.py            # BP 解析
│   ├── template_manager.py  # 模板管理
│   ├── filler.py            # 模板填充
│   ├── reviewer.py          # 审查器
│   └── utils.py             # 工具函数
├── tests/
│   └── test_all.py
├── requirements.txt
└── README.md
```

### 5.2 核心数据结构

```python
# bp_goal.py
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Action:
    id: str
    name: str
    owner: Optional[str] = None
    status: Optional[str] = None

@dataclass
class KeyResult:
    id: str
    name: str
    measure_standard: Optional[str] = None
    actions: List[Action] = None

@dataclass
class BPGoal:
    id: str
    code: str                    # P1001-6.1 / A8-2.1
    name: str
    type: str                    # "personal" | "org"
    measure_standard: Optional[str] = None
    number_anchors: List[str] = None
    key_results: List[KeyResult] = None
    status: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

@dataclass
class BPData:
    org_name: str
    person_name: Optional[str] = None
    period: str                  # "2026年度计划BP"
    goals: List[BPGoal] = None

@dataclass
class FilledTemplate:
    template_type: str           # "月报" | "季报" | "半年报" | "年报"
    org_name: str
    person_name: Optional[str]
    content: str                 # Markdown 内容
    status: str                  # "draft" | "reviewed" | "final"
    issues: List[str] = None     # 审查发现的问题
```

### 5.3 核心函数签名

```python
# input_handler.py
def parse_user_input(user_input: str) -> dict:
    """
    解析用户输入，返回：
    {
        "org_name": str,
        "person_name": Optional[str],
        "template_types": List[str]  # ["月报", "季报", "半年报", "年报"]
    }
    """

# api_client.py
class BPAPIClient:
    def __init__(self, base_url: str, app_key: str): ...
    def get_org_tree(self, period_id: str) -> dict: ...
    def get_bp_tree(self, group_id: str) -> List[dict]: ...
    def get_goal_detail(self, goal_id: str) -> dict: ...
    def fetch_bp_data(self, org_name: str, person_name: Optional[str]) -> BPData: ...

# parser.py
def parse_bp_from_api(api_data: dict) -> BPData: ...
def parse_bp_from_file(file_path: str) -> BPData: ...
def extract_number_anchors(text: str) -> List[str]: ...

# template_manager.py
class TemplateManager:
    def load_template(self, template_type: str) -> str: ...
    def get_template_structure(self, template_type: str) -> dict: ...

# filler.py
def fill_template(template: str, bp_data: BPData, template_type: str) -> str: ...
def fill_chapter_1(template: str, bp_data: BPData, template_type: str) -> str: ...
def fill_chapter_2(template: str, bp_data: BPData, template_type: str) -> str: ...
# ... 其他章节

# reviewer.py
def review_template(filled_template: FilledTemplate) -> dict:
    """
    审查填充后的模板，返回：
    {
        "passed": bool,
        "issues": List[dict]  # [{"type": "编码不匹配", "detail": "..."}]
    }
    """
```

---

## 6. 工作流设计

### 6.1 单套生成流程

```
1. 用户输入：组织名/个人名 + 生成类型
       ↓
2. InputHandler.parse_user_input() → 解析指令
       ↓
3. BPAPIClient.fetch_bp_data() → 获取 BP 数据
       ↓
4. Parser.parse_bp_from_api() → 解析为 BPData
       ↓
5. TemplateManager.load_template() → 加载目标模板
       ↓
6. Filler.fill_template() → 填充模板
       ↓
7. Reviewer.review_template() → 审查
       ↓
8. 通过？→ 输出文件 / 打回重填
```

### 6.2 多套并行生成

```python
# main.py
async def generate_templates(user_input: str) -> List[FilledTemplate]:
    # 1. 解析输入
    parsed = parse_user_input(user_input)
    template_types = parsed["template_types"]
    
    # 2. 获取 BP 数据（只获取一次）
    bp_data = api_client.fetch_bp_data(parsed["org_name"], parsed["person_name"])
    
    # 3. 并行生成多套
    tasks = [
        generate_single_template(bp_data, t_type)
        for t_type in template_types
    ]
    results = await asyncio.gather(*tasks)
    
    # 4. 返回结果
    return results
```

---

## 7. 输出规范

### 7.1 文件命名

```
{编码}_{组织名}_{姓名}_{时间维度}填写规范.md

示例：
- P001_人力资源中心_付忠明_月报填写规范.md
- A003_产品中心_林刚_季报填写规范.md
```

### 7.2 输出目录

```
projects/TPR-{YYYYMMDD}-{NNN}/规范/{组织名}_{姓名（岗位）}/
```

---

## 8. 测试用例

### 8.1 输入解析测试

| 输入 | 预期输出 |
|------|---------|
| "生成四套" | ["月报", "季报", "半年报", "年报"] |
| "只做季报" | ["季报"] |
| "月报和年报" | ["月报", "年报"] |
| "把季报和半年报给我" | ["季报", "半年报"] |

### 8.2 填充测试

| 场景 | 预期行为 |
|------|---------|
| 只有个人BP | 第2章只填P系列，组织BP标注N/A |
| 双编码体系 | P系列和A系列分开标注 |
| BP编码缺失 | 标注"[待确认编码]" |

### 8.3 审查测试

| 检查项 | 预期行为 |
|--------|---------|
| 编码不匹配 | 报错，打回重填 |
| 数字锚点缺失 | 报错，打回重填 |
| 颜色预警错误 | 报错，打回重填 |

---

## 9. 依赖关系

### 9.1 外部依赖

- Python 3.9+
- requests（HTTP 请求）
- aiohttp（异步 HTTP）
- PyYAML（配置解析）

### 9.2 内部依赖

- bp-data-fetcher（可选，提供 BP 数据获取能力）

---

## 10. 验收标准

| 验收项 | 标准 |
|--------|------|
| 输入解析 | 能正确识别组织名、个人名、生成类型 |
| API 调用 | 能正确获取 BP 数据 |
| 模板填充 | BP 原文内容正确填充到对应章节 |
| 颜色预警 | 按规则正确判断红/黄/绿 |
| 审查机制 | 能发现编码不匹配、数字缺失等问题 |
| 并行生成 | 多套模板同时生成，无阻塞 |
