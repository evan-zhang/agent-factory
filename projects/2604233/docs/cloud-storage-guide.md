# Cloud File Store 存储指南

> 适用版本：seven-policy-collector v1.3.0+
> Cloud File Store 服务地址：`http://103.236.97.248:8900`
> API 文档：见 `cloud-file-store-api-reference.md`

---

## 一、存储规则

### 1.1 路径规范

所有采集文件存储在 Cloud File Store 的 `seven-policy-collector` skill 下。

**路径公式**：
```
七大政策/{城市}/{分类目录}/{文件名}.md
```

**完整路径示例（北京）**：
```
七大政策/
└── 北京/
    ├── 01-异地就医/
    │   ├── 01-指标汇总表.md
    │   ├── 02-来源明细表.md
    │   └── 03-缺口与待补充.md
    ├── 02-异地生育报销/
    │   ├── 01-指标汇总表.md
    │   ├── 02-来源明细表.md
    │   └── 03-缺口与待补充.md
    ├── 03-公积金异地购房贷款/
    │   └── ...
    ├── 04-购房资格/
    │   └── ...
    ├── 05-车牌摇号/
    │   └── ...
    ├── 06-子女上学/
    │   └── ...
    └── 07-落户/
        └── ...
```

### 1.2 路径映射

本地路径和云端路径的关系：**去掉开头的 `./`**。

| 本地路径 | 云端路径（path 参数） |
|----------|----------------------|
| `./七大政策/北京/01-异地就医/01-指标汇总表.md` | `七大政策/北京/01-异地就医/01-指标汇总表.md` |
| `./七大政策/深圳/04-购房资格/02-来源明细表.md` | `七大政策/深圳/04-购房资格/02-来源明细表.md` |

### 1.3 文件清单

每个城市 7 个分类目录，每个目录固定 3 个文件，共 **21 个文件**。

| 文件 | 内容 | 格式 |
|------|------|------|
| `01-指标汇总表.md` | 按渠道分组的指标汇总，每个指标一行 | Markdown 表格 |
| `02-来源明细表.md` | 每行 = 一个来源支撑一个指标，含完整 URL | Markdown 表格（9列） |
| `03-缺口与待补充.md` | 缺口指标 + 缺口原因 + 已检索渠道 + 建议方向 | Markdown 表格 |

### 1.4 覆盖策略

- 同一城市同一文件重复上传会**覆盖**旧版本
- Cloud File Store 底层存储（腾讯 COS）支持多版本管理，覆盖后仍可回溯历史版本
- 每次采集完成后，该城市 21 个文件整体更新，保证数据一致性

### 1.5 认证

所有 API 调用需要在请求头携带 API Key：

```
X-API-Key: <CLOUD_FILE_STORE_KEY>
```

Key 通过环境变量 `CLOUD_FILE_STORE_KEY` 注入到运行环境，不写入 Git 仓库。

---

## 二、读取方案

### 2.1 列出已采集的城市

```bash
curl -s "http://103.236.97.248:8900/skills/seven-policy-collector/dirs/" \
  -H "X-API-Key: $CLOUD_FILE_STORE_KEY"
```

返回：
```json
{
  "path": "skills/seven-policy-collector",
  "entries": [
    {"name": "七大政策", "is_dir": true}
  ]
}
```

继续列出城市：
```bash
curl -s "http://103.236.97.248:8900/skills/seven-policy-collector/dirs/七大政策/" \
  -H "X-API-Key: $CLOUD_FILE_STORE_KEY"
```

返回：
```json
{
  "entries": [
    {"name": "北京", "is_dir": true},
    {"name": "兰州", "is_dir": true},
    {"name": "深圳", "is_dir": true}
  ]
}
```

### 2.2 列出某城市的所有文件

```bash
curl -s "http://103.236.97.248:8900/skills/seven-policy-collector/files?prefix=七大政策/北京/&recursive=true" \
  -H "X-API-Key: $CLOUD_FILE_STORE_KEY"
```

返回 21 个文件的完整列表，包含路径、大小、最后修改时间。

### 2.3 列出某分类的文件

```bash
curl -s "http://103.236.97.248:8900/skills/seven-policy-collector/dirs/七大政策/北京/01-异地就医/" \
  -H "X-API-Key: $CLOUD_FILE_STORE_KEY"
```

### 2.4 下载单个文件

```bash
curl -s "http://103.236.97.248:8900/skills/seven-policy-collector/files/七大政策/北京/01-异地就医/01-指标汇总表.md" \
  -H "X-API-Key: $CLOUD_FILE_STORE_KEY"
```

返回文件原始内容流（Markdown 文本）。

### 2.5 生成临时访问 URL

用于浏览器直接访问或分享，无需暴露 API Key：

```bash
curl -s "http://103.236.97.248:8900/skills/seven-policy-collector/url/七大政策/北京/01-异地就医/01-指标汇总表.md?expires=3600" \
  -H "X-API-Key: $CLOUD_FILE_STORE_KEY"
```

返回：
```json
{
  "url": "https://bucket.cos.region.myqcloud.com/...?q-sign-algorithm=sha1&...",
  "expires": 3600
}
```

- URL 为只读
- 有效期可设置，最长 24 小时（86400 秒）
- 任何拿到 URL 的人都可以在有效期内访问

### 2.6 搜索文件

```bash
# 按文件名关键词搜索
curl -s "http://103.236.97.248:8900/skills/seven-policy-collector/search?q=指标汇总" \
  -H "X-API-Key: $CLOUD_FILE_STORE_KEY"

# 限定搜索范围
curl -s "http://103.236.97.248:8900/skills/seven-policy-collector/search?q=缺口&prefix=七大政策/北京/" \
  -H "X-API-Key: $CLOUD_FILE_STORE_KEY"
```

### 2.7 Python 读取示例

```python
import requests

BASE = "http://103.236.97.248:8900"
KEY = "your-api-key"
HEADERS = {"X-API-Key": KEY}

def list_cities():
    """列出所有已采集城市"""
    resp = requests.get(f"{BASE}/skills/seven-policy-collector/dirs/七大政策/", headers=HEADERS)
    return [e["name"] for e in resp.json()["entries"] if e["is_dir"]]

def get_file(city, category, filename):
    """下载指定文件内容"""
    path = f"七大政策/{city}/{category}/{filename}"
    resp = requests.get(f"{BASE}/skills/seven-policy-collector/files/{path}", headers=HEADERS)
    return resp.text

def get_temp_url(city, category, filename, expires=3600):
    """生成临时访问 URL"""
    path = f"七大政策/{city}/{category}/{filename}"
    resp = requests.get(f"{BASE}/skills/seven-policy-collector/url/{path}",
                       headers=HEADERS, params={"expires": expires})
    return resp.json()["url"]

# 使用
cities = list_cities()  # → ["北京", "兰州", "深圳"]
content = get_file("北京", "01-异地就医", "01-指标汇总表.md")
url = get_temp_url("北京", "01-异地就医", "01-指标汇总表.md", expires=7200)
```

---

## 三、第三方接入指南

### 3.1 前置条件

第三方系统需要以下信息才能读取采集数据：

| 信息 | 获取方式 |
|------|----------|
| Cloud File Store 地址 | `http://103.236.97.248:8900` |
| API Key | 联系管理员分配（每个第三方使用独立 Key） |
| skill_id | `seven-policy-collector`（固定值） |

### 3.2 接入步骤

**Step 1：验证连通性**
```bash
curl -s http://103.236.97.248:8900/health \
  -H "X-API-Key: <your-key>"
# 返回 {"status":"ok"} 表示连通
```

**Step 2：发现可用城市**
```bash
curl -s "http://103.236.97.248:8900/skills/seven-policy-collector/dirs/七大政策/" \
  -H "X-API-Key: <your-key>"
```

**Step 3：读取数据**

推荐两种方式：

**方式 A：直接下载（服务端调用）**
- 适合：后端服务、定时同步、数据处理
- 每次 API 调用需携带 `X-API-Key`
- 返回原始文件流，直接解析 Markdown

**方式 B：临时 URL（前端/分享场景）**
- 适合：Web 前端展示、文件预览、临时分享
- 后端调用 `/url/{path}` 生成预签名 URL
- 前端拿到 URL 后直接访问，无需 API Key
- URL 有有效期，过期需重新生成

### 3.3 数据结构约定

第三方需要理解三个文件的内容格式：

**01-指标汇总表.md**
- Markdown 表格
- 列：渠道名称、指标名称、数值/条件、来源编号、备注
- 每行 = 一个指标的一条信息

**02-来源明细表.md**
- Markdown 表格（9 列）
- 列：来源编号、来源类型（A/B/C）、页面标题、完整 URL、发布日期、抓取日期、正文摘要、备注、缺口原因
- 每行 = 一个来源支撑一个指标

**03-缺口与待补充.md**
- Markdown 表格
- 列：渠道名称、指标名称、缺口原因、已检索渠道和关键词、建议方向
- 每行 = 一个尚未找到来源的指标

**来源类型说明**：

| 类型 | 说明 | 可信度 |
|------|------|--------|
| A | 官方来源（gov.cn / 官方公众号） | 高 |
| B | 辅助来源（本地宝、办事指南平台） | 中 |
| C | 线索来源（论坛、问答、新闻） | 低，需进一步验证 |

### 3.4 数据更新频率

- 每次采集完成后整体覆盖该城市的 21 个文件
- 没有增量更新机制，第三方应按需全量拉取或检查 `last_modified` 判断是否需要更新
- 建议轮询间隔 ≥ 1 小时（采集一次约 30-60 分钟）

### 3.5 错误处理

| HTTP 状态码 | 含义 | 处理方式 |
|-------------|------|----------|
| 200 | 成功 | 正常处理 |
| 401 | 缺少 API Key | 检查请求头 |
| 403 | API Key 错误 | 联系管理员 |
| 404 | 文件不存在 | 该城市尚未采集或路径错误 |
| 500/502 | 服务异常 | 稍后重试 |

### 3.6 注意事项

- Cloud File Store 为**只读接口**（对第三方而言），第三方不应上传、删除或修改文件
- 文件编码为 UTF-8
- 文件格式为纯 Markdown，不含 YAML frontmatter
- 单文件大小通常 < 100KB
- 如需批量导出，建议逐文件下载后本地处理
