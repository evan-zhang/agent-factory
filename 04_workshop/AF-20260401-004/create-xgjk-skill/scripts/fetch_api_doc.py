#!/usr/bin/env python3
"""
API 接口文档获取器（智能识别 URL 类型）

用途：
  根据 URL 自动识别文档类型并获取接口信息：
  - Markdown URL → 直接获取 Markdown 内容
  - Swagger URL (doc.html#/...) → 解析 Swagger JSON，提取目标接口的完整子集

使用方式：
  python3 fetch_api_doc.py <url1> [url2] ... [--output-dir <dir>]

示例：
  # Markdown 文档（自动识别）
  python3 fetch_api_doc.py "https://example.com/api-docs/im-robot.md"

  # Swagger 链接（自动识别，支持多个）
  python3 fetch_api_doc.py \
    "https://host/api-center/doc.html#/im/1.机器人管理/deleteMyRobotUsingPOST" \
    "https://host/api-center/doc.html#/im/1.机器人管理/listVisibleUsingGET" \
    --output-dir ./temp

  # 混合使用
  python3 fetch_api_doc.py "https://example.com/api.md" "https://host/api-center/doc.html#/im/xxx/someAPI"
"""

import sys
import json
import os
import gzip
import urllib.request
import urllib.error
import ssl
from urllib.parse import urlparse, unquote


# ============================================================
# 通用：HTTP 请求
# ============================================================

def _http_get(url: str, accept: str = "*/*") -> bytes:
    """通用 HTTP GET，支持 gzip，忽略 SSL 验证"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    req = urllib.request.Request(url, headers={
        "Accept": accept,
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": "SkillDocFetcher/1.0",
    })

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
            data = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip" or data[:2] == b'\x1f\x8b':
                data = gzip.decompress(data)
            return data
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} 请求 {url} 失败: {e.reason}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"请求 {url} 失败: {e.reason}")


# ============================================================
# URL 类型识别
# ============================================================

def detect_url_type(url: str) -> str:
    """
    自动识别 URL 类型：
      - 'swagger' : 包含 doc.html# 的 Swagger 链接
      - 'markdown' : 其他（默认当作 Markdown/文本文档）
    """
    parsed = urlparse(url)
    path_lower = parsed.path.lower()
    fragment = parsed.fragment

    # Swagger 特征：路径包含 doc.html 且有 hash fragment
    if "doc.html" in path_lower and fragment:
        return "swagger"

    return "markdown"


# ============================================================
# Markdown 文档获取
# ============================================================

def fetch_markdown(url: str) -> str:
    """从 URL 获取 Markdown/文本文档内容"""
    data = _http_get(url, accept="text/markdown, text/plain, */*")
    return data.decode("utf-8")


# ============================================================
# Swagger 解析（从原 parse_swagger.py 合并）
# ============================================================

def parse_swagger_url(doc_url: str) -> dict:
    """
    解析 doc.html# 链接，提取 host、serviceName、operationId。

    输入：https://host/api-center/doc.html#/im/2.消息管理/msgListByIdsUsingPOST
    返回：{ host, scheme, service_name, operation_id, swagger_url }
    """
    parsed = urlparse(doc_url)
    host = parsed.hostname
    port = parsed.port
    scheme = parsed.scheme or "https"
    fragment = unquote(parsed.fragment).lstrip("/")
    parts = fragment.split("/")

    if len(parts) < 2:
        raise ValueError(f"URL fragment 格式不正确: {fragment}")

    service_name = parts[0]
    operation_id = parts[-1]

    # 提取 doc.html 之前的路径前缀（如 /api-center）
    path = parsed.path
    doc_idx = path.lower().find("/doc.html")
    path_prefix = path[:doc_idx] if doc_idx >= 0 else ""

    # 构造正确的 origin（保留 scheme、host、port）
    if port and port not in (80, 443):
        origin = f"{scheme}://{host}:{port}"
    else:
        origin = f"{scheme}://{host}"

    swagger_url = f"{origin}{path_prefix}/{service_name}/v2/api-docs"

    return {
        "host": host, "scheme": scheme,
        "service_name": service_name,
        "operation_id": operation_id,
        "swagger_url": swagger_url,
    }


def fetch_swagger_json(swagger_url: str) -> dict:
    """获取 Swagger JSON 文档"""
    data = _http_get(swagger_url, accept="application/json")
    return json.loads(data.decode("utf-8"))


def collect_refs(obj, refs: set):
    """递归收集 $ref 引用的 definition 名称"""
    if isinstance(obj, dict):
        if "$ref" in obj:
            ref_path = obj["$ref"]
            if ref_path.startswith("#/definitions/"):
                refs.add(ref_path.split("/")[-1])
        for v in obj.values():
            collect_refs(v, refs)
    elif isinstance(obj, list):
        for item in obj:
            collect_refs(item, refs)


def resolve_all_definitions(swagger: dict, initial_refs: set) -> dict:
    """递归解析所有嵌套的 definitions"""
    all_defs = swagger.get("definitions", {})
    resolved, queue, visited = {}, list(initial_refs), set()
    while queue:
        name = queue.pop(0)
        if name in visited:
            continue
        visited.add(name)
        if name in all_defs:
            resolved[name] = all_defs[name]
            nested = set()
            collect_refs(all_defs[name], nested)
            queue.extend(r for r in nested if r not in visited)
    return resolved


def extract_api_subset(swagger: dict, operation_id: str) -> dict:
    """提取单个接口的完整 Swagger 子集"""
    for path, methods in swagger.get("paths", {}).items():
        for method, detail in methods.items():
            if isinstance(detail, dict) and detail.get("operationId") == operation_id:
                refs = set()
                collect_refs(detail, refs)
                definitions = resolve_all_definitions(swagger, refs)
                subset = {
                    "swagger": swagger.get("swagger", "2.0"),
                    "info": swagger.get("info", {}),
                    "host": swagger.get("host", ""),
                    "basePath": swagger.get("basePath", "/"),
                    "schemes": swagger.get("schemes", []),
                    "consumes": swagger.get("consumes", ["*/*"]),
                    "produces": swagger.get("produces", ["*/*"]),
                    "paths": {path: {method: detail}},
                }
                if definitions:
                    subset["definitions"] = definitions
                return subset
    raise ValueError(f"operationId not found: {operation_id}")


# ============================================================
# 统一处理入口
# ============================================================

def process_urls(urls: list, output_dir: str = None) -> list:
    """
    处理多个 URL，自动识别类型并分别处理。
    返回处理结果列表。
    """
    results = []
    swagger_cache = {}  # 缓存：同一 swagger_url 只请求一次

    for url in urls:
        url_type = detect_url_type(url)
        print(f"[识别] {url_type.upper()} — {url}", file=sys.stderr)

        try:
            if url_type == "markdown":
                # ── Markdown 文档 ──
                content = fetch_markdown(url)
                print(f"[完成] 获取 {len(content)} 字符", file=sys.stderr)

                result = {
                    "source_url": url,
                    "type": "markdown",
                    "content": content,
                }
                results.append(result)

                # 写入文件
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    # 从 URL 提取文件名
                    filename = os.path.basename(urlparse(url).path) or "api-doc.md"
                    if not filename.endswith(".md"):
                        filename += ".md"
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    print(f"[保存] {filepath}", file=sys.stderr)

            elif url_type == "swagger":
                # ── Swagger 链接 ──
                parsed = parse_swagger_url(url)
                swagger_url = parsed["swagger_url"]

                if swagger_url not in swagger_cache:
                    print(f"[获取] {swagger_url} ...", file=sys.stderr)
                    swagger_cache[swagger_url] = fetch_swagger_json(swagger_url)

                swagger = swagger_cache[swagger_url]
                subset = extract_api_subset(swagger, parsed["operation_id"])

                result = {
                    "source_url": url,
                    "type": "swagger",
                    "service_name": parsed["service_name"],
                    "operation_id": parsed["operation_id"],
                    "swagger_subset": subset,
                }
                results.append(result)

                # 写入文件
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                    filename = f"{parsed['service_name']}_{parsed['operation_id']}.json"
                    filepath = os.path.join(output_dir, filename)
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(subset, f, ensure_ascii=False, indent=2)
                    print(f"[完成] {parsed['operation_id']} -> {filepath}", file=sys.stderr)

        except Exception as e:
            print(f"[错误] {url}: {e}", file=sys.stderr)
            results.append({"source_url": url, "error": str(e)})

    return results


# ============================================================
# CLI 入口
# ============================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 fetch_api_doc.py <url1> [url2] ... [--output-dir <dir>]")
        print("")
        print("自动识别 URL 类型：")
        print("  - 包含 doc.html# → Swagger 解析模式")
        print("  - 其他 URL → Markdown 文档获取模式")
        print("  - 支持混合使用")
        print("")
        print("示例:")
        print('  python3 fetch_api_doc.py "https://example.com/api-docs/im.md"')
        print('  python3 fetch_api_doc.py "https://host/api-center/doc.html#/im/xxx/someAPI" --output-dir ./temp')
        sys.exit(1)

    urls = []
    output_dir = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--output-dir" and i + 1 < len(sys.argv):
            output_dir = sys.argv[i + 1]
            i += 2
        else:
            urls.append(sys.argv[i])
            i += 1

    if not urls:
        print("错误: 至少提供一个 URL", file=sys.stderr)
        sys.exit(1)

    results = process_urls(urls, output_dir)

    # 输出结果到 stdout
    # 如果只有一个 markdown 结果，直接输出内容（方便 AI 读取）
    if len(results) == 1 and results[0].get("type") == "markdown":
        print(results[0]["content"])
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))
