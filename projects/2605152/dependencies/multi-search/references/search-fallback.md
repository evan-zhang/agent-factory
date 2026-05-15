# 搜索降级链

## 降级顺序

```
MiniMax web_search → Tavily search → Exa AI → web_fetch → 停止
```

## 各引擎定位

| 引擎 | 定位 | 优势 | 适用场景 |
|------|------|------|----------|
| MiniMax web_search | 主力 | 中文语义理解强 | 中文政策搜索 |
| Tavily search | 回退 | 通用、国际化 | MiniMax 无结果或不可用 |
| Exa AI | 精准补充 | includeDomains 定向 | 需要限制搜索来源域名 |
| web_fetch / curl | 兜底 | 基础、无依赖 | 所有引擎不可用 |

## 切换触发条件

| 触发条件 | 动作 |
|----------|------|
| 搜索返回 0 条结果 | 切换下一个引擎，从第一轮重新开始 |
| 搜索超时（>30s） | 切换下一个引擎 |
| 搜索引擎未配置/未安装 | 跳过该引擎 |
| 搜索引擎返回错误 | 切换下一个引擎 |
| 某引擎找到结果但质量不满意 | 可补充使用下一个引擎搜索不同结果，但不替代 |

## 引擎配置检测

### MiniMax web_search
- OpenClaw：检查 `~/.mcporter/mcporter.json` 中是否有 minimax 配置
- Hermes：检查 `~/.hermes/config.yaml` 中是否有 minimax 配置
- 验证：实际调用一次 `query="探测测试"` 确认可用

### Tavily search
- 检查 `TAVILY_API_KEY` 环境变量
- 或检查 `openclaw-tavily-search` 工具是否可用
- 无需额外安装

### Exa AI
- OpenClaw：检查 mcporter 中是否有 exa 配置
- Hermes：检查 config.yaml 中是否有 exa 配置
- 需要 `EXA_API_KEY`

## 来源记录要求

每条搜索结果必须记录：
- 实际使用的搜索引擎
- 搜索查询词
- 搜索结果排名/标题/摘要
- 是否经过降级切换

## Exa 定向搜索用法

Exa 支持精准的 `includeDomains` 参数：

```
# 只搜 gov.cn 官方网站
includeDomains: ["gov.cn"]

# 只搜某城市官网
includeDomains: ["lanzhou.gov.cn"]

# 只搜教育和人社部门
includeDomains: ["edu.cn", "mohrss.gov.cn"]
```

适用场景：
- 搜索结果中官方来源太少
- 需要提高 gov.cn 页面覆盖率
- 验证某个官方网站是否存在相关内容
