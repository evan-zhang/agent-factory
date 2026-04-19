# BP 评分系统

基于 AI 的企业 BP（Business Plan）价值评分工具，支持同级权重评分、分值池分配、人工调整与奖金系数合理性审查。

## 环境要求

- Python 3.8+
- 依赖：`pip install requests pyyaml`

## 环境变量配置

```bash
export BP_APP_KEY="your_bp_app_key"       # BP系统认证key（必填）
export SCORER_API_KEY="your_openai_key"   # LLM API key（必填）
export SCORER_MODEL="gpt-4o"              # LLM模型名（可选，默认 gpt-4o）
export SCORER_API_BASE="https://api.openai.com/v1"  # LLM API地址（可选）
export BP_BASE_URL="https://your-bp-api"  # BP系统地址（可选）
```

## 快速开始

**第一步：运行评分**
```bash
python3 scripts/main.py run --org "产品中心" --period "2026Q1"
# 输出：output/产品中心-YYYYMMDD-report.md
```

**第二步（可选）：人工调整**
```bash
python3 scripts/main.py adjust \
  --report output/产品中心-20260329-report.md \
  --bp-id BP-001 --score 70 --reason "战略优先级调整"
```

**第三步：确认并锁定**
```bash
python3 scripts/main.py confirm --report output/产品中心-20260329-report.md
# 输出：output/产品中心-20260329-confirmed.md（最终版，不可修改）
```

## 文件结构

```
├── config/
│   └── scoring_weights.yaml   # 评分权重配置（可编辑）
├── output/                    # 生成的报告（自动创建）
│   ├── *-report.md            # 评分报告（可调整）
│   ├── *-confirmed.md         # 已确认版本（只读）
│   ├── *-tree.json            # 评分树缓存（供 adjust 使用）
│   └── .cross_org_cache.json  # 跨组织对标缓存
├── scripts/
│   ├── main.py                # CLI 主入口
│   ├── bp_fetcher.py          # BP数据拉取
│   ├── scorer.py              # AI评分引擎
│   ├── adjuster.py            # 人工调整模块
│   ├── report.py              # 报告生成
│   └── bonus_checker.py       # 奖金系数审查
└── tests/
    └── test_scorer.py         # 单元测试
```

## 其他命令

```bash
# 清除跨组织缓存
python3 scripts/main.py cache clear

# 运行单元测试
python3 -m pytest tests/ -v
```
