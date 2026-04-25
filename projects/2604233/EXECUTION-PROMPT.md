执行提示词：

输入：
目标城市：{目标城市}
年份/时间范围：{年份/时间范围}

=== Phase 0：环境初始化与能力探测 ===

在开始采集前，必须完成环境初始化和能力探测。

#### 0.1 MiniMax web_search 初始化

1. 运行初始化脚本：
   bash projects/2604233/scripts/setup-minimax.sh

2. 如果脚本提示需要 API Key，暂停并向用户请求：
   "需要 MiniMax Token Plan API Key 才能使用联网搜索。
    获取方式：访问 https://platform.minimax.io/subscribe/token-plan 订阅 Token Plan，
    在控制台获取 API Key（格式：sk-cp-j-xxxx...）
    请发送你的 API Key："

3. 用户提供 Key 后，将 Key 作为参数重新运行：
   bash projects/2604233/scripts/setup-minimax.sh --key <用户提供的Key>

4. 脚本会自动完成：
   - 检查/安装 uv（uvx）
   - 检查/安装 mcporter
   - 写入 MiniMax MCP 配置到 ~/.mcporter/mcporter.json
   - 验证 web_search 可用

如果环境已初始化过（mcporter 中已有 minimax 配置且验证通过），跳过此步骤。

#### 0.2 环境能力探测

完成 MiniMax 初始化后，执行以下探测，确定本次采集可用的工具链：

1. **搜索能力探测**
   - ✅ MiniMax web_search（via mcporter call minimax.web_search）— 主力搜索工具
   - 可选：Tavily search（via openclaw-tavily-search 或 API）— 通用搜索回退
   - 可选：如果 mcporter 中有 exa 配置，Exa AI 可用于定向搜索（includeDomains: ["gov.cn"]）

2. **页面抓取能力探测**
   - 用 MiniMax web_search 搜索一条测试查询
   - 从结果中选一个 gov.cn URL，尝试用 web_fetch 抓取
   - 判断 web_fetch 的 JS 渲染能力：
     - 如果能拿到完整正文（>200字）→ web_fetch 可处理 JS 页面
     - 如果拿到空壳或空白 → web_fetch 不支持 JS 渲染，标注为已知限制

3. **生成可用工具清单**
   根据探测结果，在采集开始时输出：
   ```
   本次采集可用工具：
   搜索：MiniMax web_search [已就绪]
   搜索回退：Tavily search [可用/不可用]
   搜索增强：Exa AI [可用/不可用]
   页面抓取：web_fetch [支持JS/不支持JS]
   已知限制：[如 web_fetch 不支持 JS 渲染 gov.cn 页面]
   ```

4. **工具选择策略（基于探测结果自动决定）**
   - 搜索：优先 MiniMax → Tavily → Exa → web_fetch → 都不可用则停止
   - 抓取：使用 web_fetch → 拿到空壳时在缺口表标注「JS 渲染页面，当前工具无法抓取」
   - 不自行安装额外抓取工具（Playwright 等由运行时环境提供）

=== Phase 1：政策采集 ===

请依次执行以下 7 个政策采集 skills，不要并行执行，不要合并不同 skill 的输出结果，不要跨模块读取或修改其他模块目录。

#### 全局执行要求

**搜索要求**：
1. 所有 skill 都使用同一组输入参数：目标城市 + 年份/时间范围
2. 搜索工具按 Phase 0 探测结果选择（优先 MiniMax → Tavily → Exa → web_fetch）
3. 每个 skill 必须先读取自身内置 references/*.md，再按该 reference 的渠道模板和顺序检索
4. 每次搜索查询都必须包含目标城市和年份/时间范围；如确需补充无年份政策原文，可额外检索无年份关键词，但必须在备注说明
5. 搜索不到时，尝试以下策略后再标记缺口：
   - 换用不同的关键词组合（城市名简称/别名、政策文号、部门全称/简称）
   - 换用不同的 site: 限定（从顶级域名到子域名）
   - 切换搜索引擎：MiniMax → Tavily → Exa
   - 如果 Exa 可用，用 includeDomains 定向搜索 gov.cn

**采集要求**：
6. 只做搜索、打开页面、采集、记录、写入文件；不做政策裁决
7. 每个 skill 只写入自己的固定输出目录，且每个目录只输出 3 个 Markdown 文件：
   - 01-指标汇总表.md
   - 02-来源明细表.md
   - 03-缺口与待补充.md
8. 抓取到的详细内容必须写入 02-来源明细表.md，每个指标必须能追溯到具体来源编号、页面标题和完整 URL
9. 来源明细的备注中记录：实际使用的搜索工具（MiniMax/Exa/其他）、抓取工具（web_fetch/其他）、抓取结果状态（完整/部分/JS渲染失败）
10. 如果某个指标未找到明确依据，必须写入 03-缺口与待补充.md，并记录：
    - 已检索渠道和关键词
    - 缺口原因分类：搜索无结果 / 页面无法打开 / JS渲染失败 / 内容不明确 / 其他
    - 建议的后续检索方向

#### 执行顺序

1. 使用 01-out-of-town-medical-collector
   Skill目录：projects/2604233/01-out-of-town-medical-collector/
   输出目录：./七大政策/{目标城市}/01-异地就医/

2. 使用 02-out-of-town-maternity-collector
   Skill目录：projects/2604233/02-out-of-town-maternity-collector/
   输出目录：./七大政策/{目标城市}/02-异地生育报销/

3. 使用 03-cross-city-housing-fund-loan-collector
   Skill目录：projects/2604233/03-cross-city-housing-fund-loan-collector/
   输出目录：./七大政策/{目标城市}/03-公积金异地购房贷款/

4. 使用 04-home-purchase-eligibility-collector
   Skill目录：projects/2604233/04-home-purchase-eligibility-collector/
   输出目录：./七大政策/{目标城市}/04-购房资格/

5. 使用 05-vehicle-plate-lottery-collector
   Skill目录：projects/2604233/05-vehicle-plate-lottery-collector/
   输出目录：./七大政策/{目标城市}/05-车牌摇号/

6. 使用 06-children-school-admission-collector
   Skill目录：projects/2604233/06-children-school-admission-collector/
   输出目录：./七大政策/{目标城市}/06-子女上学/

7. 使用 07-hukou-settlement-collector
   Skill目录：projects/2604233/07-hukou-settlement-collector/
   输出目录：./七大政策/{目标城市}/07-落户/

#### 采集完成报告

全部执行完成后，输出以下信息：
1. 7 个目录是否都已生成，每个目录下 3 个 Markdown 文件是否齐全
2. 工具使用统计：搜索调用次数、各工具使用占比
3. 来源质量统计：官方来源占比、辅助来源占比
4. 缺口汇总：各模块缺口数、缺口原因分类统计
5. 已知限制：哪些缺口是因为工具能力不足（如 JS 渲染失败），需要等待运行时能力升级
