# 脚本索引：`run`

| 脚本 | 鉴权 | 用途 |
|------|------|------|
| `init_run.py` | `nologin` | **自动创建**完整 `RUN_ROOT` 目录树（含中间目录）、渲染 `search_spec.json`、**规范化 `channel_bindings`（`CN_SEARCH` / 非空的 `GLOBAL_SEARCH` 均以 `minmax_web_search_mcp` 为首项）**、初始化 `run_meta` 与空 `evidence.jsonl`；若 `RUN_ROOT` 已存在则**失败退出**（不覆盖） |
| `finalize_run.py` | `nologin` | 校验必落文件、补全 `run_meta` |
| `evidence_to_catalog.py` | `nologin` | 将 **`evidence.jsonl`** 机械渲染为 **`evidence_catalog.md`**（按维度分组表；**不替代** `summary.md` / 审计结论） |

### 从 `evidence.jsonl` 生成可读浏览稿

**规范上**的人读报告是 **`summary.md`**（总控按院外 §4.1 撰写，依赖 **`audit_report.json`**）；**`gap_report.md`** 写缺口与下一步。

若仅需把 **`evidence.jsonl`** 提成按维度可读的 Markdown 清单（例如给同事快速扫链接），在同一机执行：

```bash
python3 /Users/nancy/.openclaw/workspace/skills/pharma-outpatient-orchestrator/scripts/run/evidence_to_catalog.py \
  --run-root "/Users/nancy/.openclaw/workspace/pharma-outpatient-search/network-search-runs/demo-task/深圳-院外全景/run-001"
```

默认写出 **`evidence_catalog.md`** 于该 **`RUN_ROOT`**；也可用 **`--output /path/to/file.md`** 指定路径。

## 运行示例

### 用户指定「深圳」且落在 `pharma-outpatient-search` 工作区（`demo-task` / `run-001`）

以下命令在 **`pharma-outpatient-search` workspace 根目录**执行，会**自动创建**  
`network-search-runs/demo-task/深圳-院外全景/run-001/`，并生成其中的 **`search_spec.json`**（及 `run_meta.json`、空 `evidence.jsonl`）：

```bash
cd /Users/nancy/.openclaw/workspace/pharma-outpatient-search

python3 /Users/nancy/.openclaw/workspace/skills/pharma-outpatient-orchestrator/scripts/run/init_run.py \
  --task-id "demo-task" \
  --run-id "run-001" \
  --city "深圳"
```

得到的 `search_spec.json` 路径为：

`network-search-runs/demo-task/深圳-院外全景/run-001/search_spec.json`（相对上述 `cwd`）。

### 其他城市 / run id

```bash
# 在目标工作目录执行（将写入 ./network-search-runs/...）
python3 scripts/run/init_run.py \
  --task-id "demo-task" \
  --run-id "20260424T120000Z" \
  --city "杭州"

python3 scripts/run/finalize_run.py \
  --run-root "./network-search-runs/demo-task/杭州-院外全景/20260424T120000Z"
```

路径含中文时请对 **`--run-root`** 使用实际目录字符串（与 `search_spec.city_or_topic` 规范化一致）。
