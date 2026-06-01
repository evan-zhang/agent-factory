# bd-eval-engine 架构方案审核报告

> 审核时间：2026-05-29  
> 审核人：AI架构专家  
> 审核结论：PASS WITH CONCERNS  
> 审核文档：ARCHITECTURE-REVIEW.md

---

## 一、总体评价

本架构方案整体思路清晰，技术选型基本合理，三层分离（API / Pipeline / Agent SDK）的设计思想正确。方案充分尊重了现有 Skill 的复杂度和业务规则，没有过度工程化，适合快速落地。但在 Agent SDK 选型、搜索方案的可靠性、以及一些关键技术细节上存在需要关注的风险点。

主要优点是采用了渐进式封装策略，保留了 Markdown 技能定义的可维护性，同时通过 Python 状态机确保了确定性流程的可靠性。方案的可扩展性和可替换性设计良好，符合当前 AI Agent 工程化的最佳实践。

---

## 二、肯定的设计决策

### ✅ 1. 三层分离架构合理
将确定性流程交给 Python 状态机，将智能决策交给 Agent SDK，职责清晰。避免了对确定性流程进行不必要的 LLM 推理，提高了可调试性和成本效益。

### ✅ 2. 状态管理采用文件系统方案
对于 BD 评估这种非高频、长时间运行的任务，文件系统 + state.json 的方案简单可靠。避免了数据库依赖，降低了运维复杂度，且天然支持断点续跑。

### ✅ 3. 技能定义保留 Markdown 格式
这是一个关键的正确决策。业务人员可以直接修改评估规则而不需要改代码，保证了系统的可维护性和业务敏捷性。

### ✅ 4. 并行执行策略合理
One-pager 先跑，Gate 1-3 并行，Gate 4-5 并行，Gate 6 串行的策略，既满足了依赖关系，又最大化了并行效率，预计能提速 40% 是合理的估算。

### ✅ 5. FastAPI 框架选型正确
轻量、异步支持好、自动文档生成，非常适合这种内部 API 服务。

### ✅ 6. 配置集中管理
config.yaml + 环境变量的组合方案，既保证了配置的可读性，又支持不同环境的灵活部署。

### ✅ 7. 风险缓解措施考虑周全
长任务中断、LLM 输出不稳定、API 限流等风险都有对应的缓解措施，说明方案的思考比较全面。

---

## 三、需要改进的问题

### 🔴 严重问题 1：OpenAI Agents SDK 选型风险

**问题描述**：
OpenAI Agents SDK 是一个相对较新的库（2024年底发布），生态成熟度不如 LangGraph/LangChain。对于生产环境的关键任务，存在以下风险：

- 文档不完善，遇到问题时难以找到解决方案
- 社区经验少，最佳实践尚未形成共识
- 潜在的未知 bug 和稳定性问题
- 长期维护的不确定性

**建议方案**：
1. **短期方案**：在 POC 阶段先使用 OpenAI Agents SDK，但做一层抽象封装。如果遇到无法解决的问题，可以快速切换到替代方案。
2. **推荐替代方案**：**LlamaIndex Workflows**（推荐度：⭐⭐⭐⭐⭐）
   - 轻量级，与 OpenAI Agents SDK 复杂度相当
   - 成熟度高，文档完善，社区活跃
   - 原生支持工具调用和 RAG
   - 模型无关，可接任何 OpenAI 兼容 API
   - 已有大量生产环境案例

3. **备选方案**：**LangGraph**（推荐度：⭐⭐⭐⭐）
   - 虽然较重，但成熟度和稳定性最高
   - 对于这种复杂的多 Agent 协作场景，LangGraph 的状态管理和错误处理更完善
   - 如果团队有 LangChain 经验，学习成本可以接受

**具体建议**：
- 在项目初期进行技术选型的快速 POC（3-5天）
- 用相同的功能需求，分别用 OpenAI Agents SDK 和 LlamaIndex Workflows 实现
- 对比易用性、稳定性、文档质量、社区支持度
- **建议优先选择 LlamaIndex Workflows**

---

### 🔴 严重问题 2：Tavily 搜索在中国市场的可靠性未验证

**问题描述**：
方案中提到使用 Tavily 作为搜索引擎，但未验证其在中国市场的可用性：

- Tavily 服务器主要在海外，可能被 GFW 阻断
- 搜索结果可能偏向海外内容，对国内医药市场信息的覆盖不足
- API 延迟可能较高，影响 60-80 分钟的总时长估算

**建议方案**：
1. **主搜索引擎**：使用 **MiniMax Search API**
   - 国内服务，速度快
   - 对中文内容友好
   - 已在现有 Skill 中验证过
   - 提供结构化输出

2. **辅助搜索引擎**：Tavily（可选）
   - 用于搜索海外医药信息（FDA/EMA/临床试验等）
   - 只在需要海外信息时调用
   - 配置请求超时（3秒）和 fallback

3. **搜索策略调整**：
   ```python
   # 伪代码
   if domain == "domestic":
       use_minimax_search()
   elif domain == "international":
       use_tavily_search()  # 需配置代理
   else:
       use_both_and_merge()
   ```

**具体建议**：
- 在技术验证阶段，用 5-10 个实际品种测试 Tavily 的可用性
- 如果连接不稳定，直接改用 MiniMax 作为主搜索引擎
- 搜索结果的质量比搜索引擎的"AI Agent 专用性"更重要

---

### 🟡 中等问题 3：asyncio 并行策略缺少并发控制

**问题描述**：
方案中提到用 asyncio 并行执行 Gate 评估，但未提到并发控制。这可能导致：

- 同时向 LLM API 发送过多请求，触发速率限制
- 搜索 API 并发过高，被限流或封禁
- 内存占用过高，系统资源耗尽

**建议方案**：
1. **使用信号量控制并发数**：
   ```python
   # 伪代码
   MAX_CONCURRENT_AGENTS = 3
   semaphore = asyncio.Semaphore(MAX_CONCURRENT_AGENTS)
   
   async def run_gate(gate_id):
       async with semaphore:
           return await evaluator_agent.evaluate(gate_id)
   
   # 并行执行 Gate 1-3
   results = await asyncio.gather(
       run_gate(1), run_gate(2), run_gate(3)
   )
   ```

2. **搜索请求的速率限制**：
   ```python
   # 搜索之间添加间隔，避免触发限流
   async for search in searches:
       result = await search_api.query(search)
       await asyncio.sleep(1)  # 间隔1秒
   ```

3. **资源监控和降级**：
   - 监控系统内存和 API 调用速率
   - 超过阈值时自动降低并发数
   - 记录到执行日志，便于优化

---

### 🟡 中等问题 4：state.json 并发安全性未考虑

**问题描述**：
方案中用 state.json 管理状态，但未考虑并发写入的问题。在以下场景可能出现数据损坏：

- 用户同时发起多个请求更新同一个品种
- API 的多个端点同时写入 state.json
- 进程被强制中断时写入不完整

**建议方案**：
1. **使用文件锁**：
   ```python
   import fcntl
   
   def update_state(case_id, updates):
       with open('state.json', 'r+') as f:
           fcntl.flock(f.fileno(), fcntl.LOCK_EX)
           state = json.load(f)
           state.update(updates)
           f.seek(0)
           json.dump(state, f, indent=2)
           f.truncate()
           fcntl.flock(f.fileno(), fcntl.LOCK_UN)
   ```

2. **原子写入**：
   ```python
   def update_state(case_id, updates):
       # 先写到临时文件
       temp_file = f'state.json.tmp.{os.getpid()}'
       with open(temp_file, 'w') as f:
           json.dump(updates, f, indent=2)
       
       # 原子性重命名
       os.replace(temp_file, 'state.json')
   ```

3. **添加乐观锁**：
   ```json
   {
     "version": 5,
     "updatedAt": "2026-05-29T10:00:00Z",
     "content": { ... }
   }
   ```
   更新时检查版本号，避免覆盖较新的更新。

---

### 🟡 中等问题 5：子 Agent 超时处理机制不够完善

**问题描述**：
方案中提到"子 Agent 超时应对"，但策略较为粗糙（记录完成到第几个 Gate，主会话补全）。对于 60-80 分钟的长任务，这个策略可能导致：

- 大量工作被浪费
- 难以复现和调试超时问题
- 用户等待时间过长

**建议方案**：
1. **分层超时设置**：
   ```python
   TIMEOUTS = {
       "discovery": 600,      # 10分钟
       "gate_evaluation": 900,  # 15分钟/Gate
       "battle_round": 600,   # 10分钟/轮
       "total_case": 5400     # 90分钟总超时
   }
   ```

2. **超时后的智能恢复**：
   - 记录超时发生的具体步骤和上下文
   - 保存中间结果到 checkpoint 文件
   - 支持从超时点恢复，而非从头开始

3. **超时原因分类**：
   ```python
   enum TimeoutReason:
       LLM_API_TIMEOUT = "llm_api_timeout"
       SEARCH_API_TIMEOUT = "search_api_timeout"
       NETWORK_ERROR = "network_error"
       LLM_HALLUCINATION_LOOP = "llm_loop"  # LLM 进入无限循环
   ```

4. **重试策略**：
   - LLM 超时：重试 2 次，换 prompt
   - 搜索超时：切换到备用搜索引擎
   - 网络错误：指数退避重试

---

### 🟢 轻微问题 6：技能 Markdown 运行时读取的性能影响

**问题描述**：
方案中每次执行 Gate 评估时都从磁盘读取对应的 Markdown 技能定义文件，这会带来：

- 磁盘 I/O 开销（虽然不大）
- 如果技能文件很多，会有文件系统压力
- 每次都需要解析 Markdown

**优化建议**：
1. **启动时预加载和缓存**：
   ```python
   # 在 API 启动时加载所有技能到内存
   skill_cache = {}
   for skill_file in glob("skills/*.md"):
       skill_name = Path(skill_file).stem
       with open(skill_file) as f:
           skill_cache[skill_name] = f.read()
   ```

2. **监控缓存命中率**：
   - 记录缓存命中/未命中情况
   - 如果发现频繁读取，可以加缓存层

3. **当前方案也可接受**：
   - 如果技能文件不频繁修改，当前方案已经足够
   - 简单直接，避免过度优化
   - 等实际性能瓶颈出现再优化

---

### 🟢 轻微问题 7：API 设计缺少部分管理端点

**问题描述**：
当前 API 设计只有核心的评估端点，缺少一些管理功能：

- 无法查询已评估的品种列表
- 无法删除误创建的品种
- 无法查询系统健康状态
- 无法查询配置信息

**补充建议**：
添加以下端点：

```yaml
# 补充的 API 端点

GET /cases:
  描述: 查询已评估的品种列表
  参数: limit, offset, status
  响应: { cases: [...], total: 100 }

GET /health:
  描述: 健康检查端点
  响应: { status: "healthy", checks: {...} }

DELETE /cases/{case_id}:
  描述: 删除品种目录（谨慎操作）
  请求体: { confirm: true }

GET /config:
  描述: 查询当前配置（不包含敏感信息）
  响应: { model: {...}, search: {...} }

GET /cases/{case_id}/logs:
  描述: 获取执行日志
  响应: execution-log.md 内容
```

---

## 四、补充建议

### 💡 建议 1：添加可观测性（Observability）

对于这种长时间运行的多步骤任务，可观测性至关重要：

```python
# 1. 结构化日志
import structlog
logger = structlog.get_logger()

logger.info("gate_started", 
            case_id=case_id, 
            gate_id=gate_id, 
            phase="gate_evaluation")

# 2. 指标收集
from prometheus_client import Counter, Histogram

gate_duration = Histogram('gate_duration_seconds', 'Gate execution time', ['gate_id'])
llm_calls = Counter('llm_calls_total', 'Total LLM calls', ['model', 'endpoint'])

# 3. 分布式追踪
# 用 OpenTelemetry 追踪完整的评估流程
```

**价值**：
- 快速定位性能瓶颈
- 监控 LLM 调用成本
- 追踪错误发生的完整上下文

---

### 💡 建议 2：添加 LLM 成本监控

医药 BD 评估会大量调用 LLM，成本控制很重要：

```python
# 成本追踪
class CostTracker:
    def __init__(self):
        self.costs = {}
    
    def record_call(self, model, input_tokens, output_tokens):
        cost = calculate_cost(model, input_tokens, output_tokens)
        self.costs[model] = self.costs.get(model, 0) + cost
        
    def get_report(self):
        return {
            "total_cost": sum(self.costs.values()),
            "by_model": self.costs
        }

# 在 state.json 中记录成本
{
  "cost": {
    "total": 15.67,
    "by_model": {
      "glm-5.1": 12.34,
      "gpt-4o": 3.33
    },
    "by_phase": {
      "discovery": 2.5,
      "gate_evaluation": 10.0,
      "battle": 3.17
    }
  }
}
```

---

### 💡 建议 3：添加技能定义的版本管理

当前方案中，技能定义是静态的 Markdown 文件。当技能规则更新时，可能导致：

- 已完成的评估与新规则不一致
- 难以追溯某个评估是用哪个版本的规则做的

**建议方案**：
```yaml
# skills/VERSION.yaml
version: "1.2.0"
updated_at: "2026-05-29"
changes:
  - "Gate 2 财务门槛调整"
  - "Gate 5 新增合规检查项"

# 在 state.json 中记录
{
  "skillVersion": "1.2.0",
  "skillFilesHash": "sha256:..."  # 所有技能文件的 hash
}
```

---

### 💡 建议 4：考虑增量更新的实现复杂度

方案中提到了"增量更新"功能，但没有详细说明实现细节。这个功能可能比预期的复杂：

1. **依赖关系分析**：更新 Gate 3 可能需要级联更新 Gate 6
2. **版本兼容性**：旧版本 Gate 文件的结构可能不兼容
3. **Battle 审查范围**：只审查变更的 Gate，还是重新审查整体逻辑？

**建议**：
- 在第一版中先不支持增量更新，只支持全量评估
- 积累足够经验后再实现增量更新
- 或者实现一个简化版：只支持单个 Gate 的重新评估（不处理级联关系）

---

### 💡 建议 5：添加评估模板管理功能

对于经常评估的同类品种（如同一适应症的不同产品），可以预填充部分内容：

```yaml
# templates/biotech-oncology-template.yaml
name: "生物抗肿瘤药评估模板"
product_type: "生物类似药"
financial_threshold_type: "创新药"
predefined_answers:
  gate_2_premise:
    - "适应症市场容量如何？"
    - "竞品格局和市占率估算？"
  gate_3_evidence:
    - "临床试验设计是否合理？"
    - "注册路径和获批时间估算？"
```

这样可以减少重复工作，提高评估效率。

---

### 💡 建议 6：考虑多语言支持的扩展性

如果将来需要评估海外品种，可能需要支持英文或其他语言：

```python
# 在 config.yaml 中添加
localization:
  default_language: "zh-CN"
  supported_languages: ["zh-CN", "en-US"]
  skill_files:
    zh-CN: "skills/"
    en-US: "skills-en/"
```

虽然当前需求不支持，但在架构设计时可以考虑这个扩展性。

---

### 💡 建议 7：添加 Agent 回放和调试功能

对于复杂的 LLM 应用，调试和复现问题很困难：

```python
# 记录每次 Agent 调用的完整上下文
{
  "agent_call": {
    "id": "call_abc123",
    "timestamp": "2026-05-29T10:00:00Z",
    "agent_type": "GateEvaluator",
    "input": { ... },
    "output": { ... },
    "tools_called": [...],
    "llm_requests": [
      {
        "model": "glm-5.1",
        "prompt": "...",
        "response": "..."
      }
    ],
    "duration_ms": 15000
  }
}
```

这样可以：
- 复现问题场景
- 分析 LLM 调用模式
- 优化 prompt

---

### 💡 建议 8：考虑 Docker 部署的配置注入

方案中提到 Docker 部署，但没有说明配置注入方式：

```dockerfile
# 推荐方案：环境变量 + ConfigMap
ENV MODEL_API_KEY=${MODEL_API_KEY}
ENV TAVILY_API_KEY=${TAVILY_API_KEY}
ENV OUTPUT_ROOT=/data/cases

# 或者使用 Kubernetes ConfigMap/Secret
```

这样可以：
- 避免在镜像中包含敏感配置
- 不同环境使用不同配置
- 支持配置的热更新

---

## 五、技术选型补充说明

### 5.1 为什么推荐 LlamaIndex Workflows

| 维度 | OpenAI Agents SDK | LlamaIndex Workflows | LangGraph |
|------|------------------|---------------------|-----------|
| 成熟度 | ⭐⭐ 新项目 | ⭐⭐⭐⭐⭐ 生产验证 | ⭐⭐⭐⭐⭐ 生产验证 |
| 文档质量 | ⭐⭐⭐ 一般 | ⭐⭐⭐⭐⭐ 完善 | ⭐⭐⭐⭐⭐ 完善 |
| 学习曲线 | ⭐⭐⭐⭐ 平缓 | ⭐⭐⭐⭐ 平缓 | ⭐⭐⭐ 陡峭 |
| 轻量度 | ⭐⭐⭐⭐⭐ 轻量 | ⭐⭐⭐⭐ 轻量 | ⭐⭐ 较重 |
| 工具生态 | ⭐⭐⭐ 发展中 | ⭐⭐⭐⭐⭐ 丰富 | ⭐⭐⭐⭐⭐ 最丰富 |
| 模型无关性 | ⭐⭐⭐⭐⭐ 支持 | ⭐⭐⭐⭐⭐ 支持 | ⭐⭐⭐⭐⭐ 支持 |
| 生产案例 | ⭐⭐ 较少 | ⭐⭐⭐⭐ 多 | ⭐⭐⭐⭐⭐ 最多 |
| 长期维护性 | ⭐⭐⭐ 不确定 | ⭐⭐⭐⭐ 确定 | ⭐⭐⭐⭐⭐ 确定 |

**LlamaIndex Workflows 的优势**：
- 声明式定义工作流，类似 LangGraph 但更轻量
- 内置 RAG 支持，适合需要读取技能定义的场景
- 优秀的 observability 和调试工具
- 活跃的社区和快速的 issue 响应

**代码示例对比**：

```python
# LlamaIndex Workflows（推荐）
from llama_index.core.workflow import Workflow

class EvaluationWorkflow(Workflow):
    async def run(self, product_name: str):
        # Step 1: Discovery
        discovery_result = await self.run_agent(
            "discovery_agent",
            context={"product": product_name}
        )
        
        # Step 2: Routing
        route = await self.run_agent(
            "router_agent", 
            context=discovery_result
        )
        
        # Step 3-5: 并行评估
        gates = await self.run_parallel([
            ("gate_1", {...}),
            ("gate_2", {...}),
            ("gate_3", {...})
        ])
        
        return gates
```

---

### 5.2 为什么推荐 MiniMax 作为主搜索引擎

| 维度 | Tavily | MiniMax | SerpAPI |
|------|-------|---------|---------|
| 国内访问速度 | ⭐⭐ 慢 | ⭐⭐⭐⭐⭐ 快 | ⭐⭐⭐ 一般 |
| 中文内容质量 | ⭐⭐⭐ 一般 | ⭐⭐⭐⭐⭐ 优秀 | ⭐⭐⭐ 一般 |
| 结构化输出 | ⭐⭐⭐⭐⭐ 支持 | ⭐⭐⭐⭐ 支持 | ⭐⭐⭐ 一般 |
| 免费额度 | 1000次/月 | 限制较松 | 100次/月 |
| 医药信息覆盖 | ⭐⭐⭐⭐ 海外好 | ⭐⭐⭐⭐ 国内好 | ⭐⭐⭐ 一般 |

**推荐策略**：
- **主搜索引擎**：MiniMax（覆盖国内医药信息）
- **辅助搜索引擎**：Tavily（覆盖 FDA/EMA/海外临床试验）
- **备选方案**：SerpAPI（兜底）

---

## 六、实施建议

### 6.1 阶段性实施计划

**Phase 1：技术验证（1-2周）**
- [ ] 验证 LlamaIndex Workflows 可行性
- [ ] 验证 MiniMax/Tavily 搜索可用性
- [ ] 做一个单品种的完整 POC
- [ ] 测试性能和成本

**Phase 2：MVP 开发（3-4周）**
- [ ] 实现核心 Pipeline 层
- [ ] 实现单个 Agent（先做 Discovery Agent）
- [ ] 实现状态管理和断点续跑
- [ ] 部署到测试环境

**Phase 3：完整功能（4-6周）**
- [ ] 实现所有 Agent
- [ ] 实现并行调度
- [ ] 实现报告生成
- [ ] 添加可观测性

**Phase 4：优化和上线（2-3周）**
- [ ] 性能优化
- [ ] 成本优化
- [ ] 压力测试
- [ ] 正式上线

### 6.2 风险监控指标

```yaml
关键指标:
  性能:
    - 品种评估总时长（目标：<80 分钟）
    - 单个 Gate 平均时长（目标：<15 分钟）
    - API 响应时间（目标：<500ms）
  
  可靠性:
    - 任务成功率（目标：>95%）
    - 断点续跑成功率（目标：100%）
    - LLM API 调用成功率（目标：>99%）
  
  成本:
    - 单品种平均成本（目标：<20元）
    - LLM 调用次数（目标：<300次/品种）
    - 搜索 API 调用次数（目标：<50次/品种）
```

---

## 七、结论

### 最终结论：PASS WITH CONCERNS ✅ ⚠️

**可以通过，但需要关注以下关键问题**：

1. **必须解决**：
   - ✅ 在技术验证阶段（1-2周）验证 LlamaIndex Workflows 替代 OpenAI Agents SDK
   - ✅ 在技术验证阶段验证 MiniMax/Tavily 搜索的可用性
   - ✅ 添加并发控制和文件锁机制

2. **强烈建议**：
   - ✅ 添加可观测性（日志、指标、追踪）
   - ✅ 添加成本监控
   - ✅ 添加健康检查和管理 API
   - ✅ 在 MVP 阶段先不支持增量更新

3. **可选优化**：
   - 🔄 技能定义预加载和缓存
   - 🔄 Agent 回放和调试功能
   - 🔄 评估模板管理

### 总体评价

这个架构方案的**整体思路是正确的**，三层分离的设计思想值得肯定。主要的风险集中在技术选型的成熟度上，但这些风险都是可以通过技术验证阶段来识别和缓解的。

**建议采取渐进式的实施策略**：
1. 先用 1-2 周做技术验证，确认核心技术的可行性
2. 用 3-4 周开发 MVP，跑通一个完整品种的评估
3. 在 MVP 成功的基础上，再扩展完整功能

如果在技术验证阶段发现 LlamaIndex Workflows 或搜索方案有重大问题，可以及时调整，避免大量投入后的返工。

### 推荐的技术栈

```yaml
推荐配置:
  Agent SDK: LlamaIndex Workflows
  搜索引擎: MiniMax（主） + Tavily（辅，可选）
  API框架: FastAPI
  状态管理: 文件系统 + state.json + 文件锁
  任务队列: asyncio + 信号量控制
  可观测性: structlog + prometheus_client + OpenTelemetry
  部署方式: Docker + 环境变量注入
```

---

## 附录：快速参考

### A. 关键决策清单

| 决策点 | 方案选择 | 理由 | 风险 |
|-------|---------|------|------|
| Agent SDK | **LlamaIndex Workflows** | 成熟、文档好、轻量 | 需要1-2周验证 |
| 搜索引擎 | **MiniMax 为主** | 国内快、中文好 | 需要验证质量 |
| 并发控制 | **asyncio + Semaphore** | 简单有效 | 需要调优参数 |
| 状态管理 | **文件 + JSON + 文件锁** | 简单、可靠 | 并发安全性 |
| 可观测性 | **structlog + Prometheus** | 生产标准 | 学习成本 |

### B. 技术验证检查清单

```yaml
技术验证阶段（1-2周）必须完成的检查:
  
  检查项1: LlamaIndex Workflows 验证
    - [ ] 实现 Discovery Agent
    - [ ] 实现工具调用
    - [ ] 测试错误处理
    - [ ] 测试性能和稳定性
  
  检查项2: 搜索引擎验证
    - [ ] MiniMax 搜索 10 个医药品种
    - [ ] Tavily 搜索 5 个海外品种
    - [ ] 对比结果质量
    - [ ] 测试 API 延迟和限流
  
  检查项3: 端到端 POC
    - [ ] 选择一个典型品种
    - [ ] 跑通 Phase 1-5.5
    - [ ] 测试断点续跑
    - [ ] 测试异常恢复
  
  检查项4: 性能和成本测试
    - [ ] 记录总耗时
    - [ ] 记录 LLM 调用次数和成本
    - [ ] 记录搜索 API 调用次数
    - [ ] 评估是否满足目标
```

### C. 推荐阅读材料

1. **LlamaIndex Workflows 官方文档**
   https://docs.llamaindex.ai/en/latest/module_guides/workflow/

2. **MiniMax Search API 文档**
   https://www.minimaxi.com/document

3. **Asyncio 并发最佳实践**
   https://docs.python.org/3/library/asyncio.html

4. **Python 文件锁实现**
   https://docs.python.org/3/library/fcntl.html

---

**审核完成时间**：2026-05-29  
**下次审核建议**：技术验证阶段完成后（约2周后）
