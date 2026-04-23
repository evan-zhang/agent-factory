执行提示词：

输入：
目标城市：{目标城市}
年份/时间范围：{年份/时间范围}

=== Phase 0：环境初始化（首次执行必做）===

在开始采集前，必须先确认 MiniMax web_search 环境可用。

请按以下步骤执行：

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

5. 初始化完成后，继续执行下面的采集流程。

如果环境已初始化过（mcporter 中已有 minimax 配置且验证通过），跳过此步骤。

=== Phase 1：政策采集 ===

请依次执行以下 7 个政策采集 skills，不要并行执行，不要合并不同 skill 的输出结果，不要跨模块读取或修改其他模块目录。

全局执行要求：
1. 所有 skill 都使用同一组输入参数：
 - 目标城市
 - 年份/时间范围
2. 必须使用 MiniMax web_search（via mcporter call minimax.web_search）进行检索。如 MiniMax 不可用，回退到 web_fetch。
3. 每个 skill 必须先读取自身内置 references/*.md，再按该 reference 的渠道模板和顺序检索。
4. 每次搜索查询都必须包含目标城市和年份/时间范围；如确需补充无年份政策原文，可额外检索无年份关键词，但必须在备注说明。
5. 只做搜索、打开页面、采集、记录、写入文件；不做政策裁决。
6. 每个 skill 只写入自己的固定输出目录，且每个目录只输出 3 个 Markdown 文件：
 - 01-指标汇总表.md
 - 02-来源明细表.md
 - 03-缺口与待补充.md
7. 抓取到的详细内容必须写入 02-来源明细表.md，每个指标必须能追溯到具体来源编号、页面标题和完整 URL。
8. 如果某个指标未找到明确依据，必须写入 03-缺口与待补充.md，并记录已检索渠道、关键词和当前边界。

请按以下顺序逐个执行：

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

全部执行完成后，只简要告诉我 7 个目录是否都已生成，以及每个目录下 3 个 Markdown 文件是否齐全。
