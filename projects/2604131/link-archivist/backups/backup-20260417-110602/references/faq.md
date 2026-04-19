# 常见问题

## 转录失败

### xgjk_app_key 未配置
**现象**：YouTube 视频跳过转录
**处理**：
1. 联系管理员获取玄关 appKey
2. 添加到配置文件：`"xgjk_app_key": "xxx"`
3. 重新运行转录

### AI 慧记任务超时
**现象**：转录超过 10 分钟未完成
**处理**：
1. 检查音频文件大小（建议 < 100MB）
2. 检查网络连接
3. 仍失败 → 只用标题+描述生成报告

---

## 抓取失败

### r.jina.ai 超时
**现象**：curl 抓取超时或返回空
**处理**：
1. 重试一次，加大 `--max-time` 到 30s
2. 仍失败 → 用 `web_search` 补充信息
3. 都失败 → 提示用户手动复制正文

### YouTube 无法下载
**现象**：yt-dlp 返回错误
**处理**：
1. 检查是否是短链接（需要展开）
2. 检查是否需要登录
3. 仍失败 → 只抓标题+描述，跳过转录

### 抖音防爬
**现象**：r.jina.ai 抓取失败
**处理**：提示用户"抖音有防爬机制，请手动复制正文发给我"

### 今日头条返回空内容
**现象**：r.jina.ai 对今日头条移动端短链接（m.toutiao.com/is/xxx）返回空内容
**处理**：
1. 使用 BeautifulSoup + requests 直接抓取（加移动端 User-Agent）
2. 解析 article 标签或 application/ld+json 数据
3. 仍失败 → 用 `web_search` 搜索关键信息

```python
import requests
from bs4 import BeautifulSoup

url = 'https://m.toutiao.com/is/xxx/'
headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'}
r = requests.get(url, headers=headers, timeout=10)
soup = BeautifulSoup(r.text, 'html.parser')
article = soup.find('article')
if article:
    for tag in article(['script', 'style']):
        tag.decompose()
    text = article.get_text(' ', strip=True)
```

---

## 配置问题

### 配置文件找不到
**现象**：init_config.py 返回未配置
**处理**：
1. 检查环境变量（OPENCLAW_ROOT / HERMES_HOME）
2. 手动创建配置文件到对应目录
3. 运行 init_config.py 验证

### archive_dir 权限不足
**现象**：归档时报错 "Permission denied"
**处理**：
1. 检查目录是否存在
2. 检查写权限
3. 手动创建目录：`mkdir -p {archive_dir}`

---

## 编号问题

### 编号重复
**现象**：同一天内编号冲突
**处理**：
1. 检查当日目录下已有文件
2. archive_report.py 会自动取最大编号 +1
3. 仍冲突 → 手动删除冲突文件

### 编号格式错误
**现象**：不是 K-YYMMDD-NNN 格式
**处理**：检查 archive_report.py 是否正确执行

---

## 工具缺失

### curl 未安装
**现象**：抓取内容失败
**处理**：`apt-get install curl` 或 `yum install curl`

### python3 未安装
**现象**：脚本无法执行
**处理**：安装 Python 3.8+

---

## 平台特定

### Hermes 环境
- 配置路径：`~/.hermes/link-archivist-config.json`
- 工具映射：见 SKILL.md "工具映射" 章节

### OpenClaw 环境
- 配置路径：`~/.openclaw/link-archivist-config.json`
- 可用工具：web_fetch, exec, write

### 其他环境
- 配置路径：`~/.config/link-archivist-config.json`
- 需自行适配工具调用
