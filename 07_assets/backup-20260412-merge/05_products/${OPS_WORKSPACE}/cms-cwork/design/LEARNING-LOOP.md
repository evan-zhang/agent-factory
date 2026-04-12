# cms-cwork — 学习建议记录

## 核心学习要点

### 1. Agent-First 架构思想
- **理解**: Agent 负责业务逻辑，脚本负责 API 编排
- **实践**: 将复杂业务决策与标准化 API 调用分离
- **应用**: 其他 Skill 可采用相同架构模式

### 2. Python 编排脚本设计模式
- **结构**: argparse 参数解析 → API 调用 → JSON 输出
- **错误处理**: stdout 输出业务数据，stderr 输出调试信息
- **扩展性**: 通过共享客户端层减少重复代码

### 3. JSON 协议规范
- **成功格式**: `{"success": true, "data": {...}}`
- **失败格式**: `{"success": false, "error": "消息"}`
- **交互模式**: 支持干跑预览和交互式确认

## 设计模式迁移

### 从 TypeScript 到 Python
- **变化**: TypeScript 类封装 → Python 函数式编程
- **优势**: 更轻量，无环境依赖，易于调试
- **挑战**: 需要手动参数校验和错误处理

### 从源码到编排脚本
- **变化**: 源码直接调用 → 脚本化 API 编排
- **优势**: 标准化接口，便于组合，易于维护
- **挑战**: 需要设计清晰的命令行参数

## 关键决策记录

### 决策1: 选择 Python 作为脚本语言
- **原因**: 相比 Node.js 更轻量，无需 npm 环境
- **依据**: Agent 调用外部脚本的场景下，Python 更通用
- **教训**: 需要处理 Python 2/3 兼容性问题

### 决策2: 单一脚本单一职责
- **原因**: 便于测试和维护，符合单一职责原则
- **效果**: 每个脚本专注一个业务域，易于理解和使用
- **经验**: 功能拆分有助于模块化复用

### 决策3: JSON 输出协议
- **原因**: 便于 Agent 解析和处理
- **效果**: 标准化数据交换格式，易于扩展
- **经验**: 成功/失败统一格式减少了 Agent 的解析复杂度

## 最佳实践总结

### 1. 脚本设计
```python
# 命令行参数设计
parser.add_argument("--required", required=True, help="必填参数")
parser.add_argument("--optional", default="default", help="可选参数")

# 错误处理
try:
    result = api_call()
    print(json.dumps({"success": True, "data": result}))
except Exception as e:
    print(json.dumps({"success": False, "error": str(e)}), file=sys.stderr)
```

### 2. API 客户端封装
```python
class CWorkClient:
    def __init__(self, app_key, base_url):
        self.app_key = app_key
        self.base_url = base_url
    
    def api_call(self, endpoint, params):
        # 统一 HTTP 请求逻辑
        # 统一错误处理
        # 统一响应解析
```

### 3. 版本管理
- 主版本号变更：重大架构调整
- 次版本号变更：新增功能
- 修订版本号变更：Bug 修复

## 技术债记录

### 1. 错误码标准化
- **问题**: 当前错误信息不够结构化
- **解决方案**: 定义错误码和错误信息映射
- **优先级**: 中等，不影响基本使用

### 2. 重试机制
- **问题**: 网络错误时缺乏自动重试
- **解决方案**: 在客户端层添加指数退避重试
- **优先级**: 中等，网络环境好的情况下影响不大

### 3. 缓存策略
- **问题**: 频繁查询相同数据效率低
- **解决方案**: 对不常变化的数据添加内存缓存
- **优先级**: 低，当前使用场景频次不高

## 可复用模式

### 1. Agent-First Skill 架构
**适用场景**: 需要与外部 API 集成的 Skill
**核心思想**: 业务逻辑交给 Agent，API 调用交给脚本
**实施步骤**: 
1. 设计 JSON 输出协议
2. 编写标准化编排脚本
3. Agent 通过 JSON 交互使用脚本

### 2. Python 编排脚本模式
**适用场景**: 需要命令行工具化的 API 集成
**核心思想**: argparse + API 调用 + JSON 输出
**实施步骤**:
1. 设计清晰的命令行参数
2. 封装共享客户端层
3. 统一错误处理和输出格式

### 3. 设计文档体系
**适用场景**: 有设计变更和讨论的 Skill
**核心思想**: 记录设计决策和变更历史
**实施步骤**:
1. DISCUSSION-LOG.md 记录讨论过程
2. DESIGN.md 记录架构设计
3. LEARNING-LOOP.md 记录经验教训
4. SHARE-LOG.jsonl 记录对外分享

---

*最后更新: 2026-04-03*