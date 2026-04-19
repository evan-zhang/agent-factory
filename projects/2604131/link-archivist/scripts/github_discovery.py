#!/usr/bin/env python3
"""
GitHub 项目发现脚本
输入文本，输出其中发现的 GitHub 项目 URL 和项目名
"""
import sys
import re
import json
import urllib.request
import urllib.parse

GITHUB_API = "https://api.github.com"

def find_github_urls(text):
    """从文本中找到 github.com URL"""
    pattern = r'github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)'
    found = set()
    for match in re.finditer(pattern, text, re.IGNORECASE):
        owner, repo = match.group(1), match.group(2)
        repo = repo.rstrip('/').rstrip(')')
        if owner.lower() not in ['com', 'org', 'io'] and len(owner) > 1:
            found.add(f"https://github.com/{owner}/{repo}")
    return list(found)

def extract_project_names(text):
    """从文本中提取可能是项目名的词组（用于无明确链接时搜索）"""
    # 常见项目名：带大写的 CamelCase、全大写词（GPT、API、LLM）、kebab-case
    patterns = [
        r'["\u201c\u201d]([A-Z][a-zA-Z0-9_-]+)["\u201c\u201d]',
        r"'([^']+)'",
        r'\uff08([^\uff09]+)\uff09',  # 中文括号
        r'\b([A-Z][a-zA-Z0-9]+)\b',  # 大写字母开头的词: AutoGPT, GitHub, GPT4
        r'\b([a-z]+[-_][a-z]+)\b',  # kebab-case
    ]
    blocked = {'github', 'google', 'microsoft', 'facebook', 'amazon', 'apple', 'example'}
    seen = set()
    candidates_filtered = []
    for p in patterns:
        for m in re.finditer(p, text):
            name = m.group(1).strip()
            if len(name) > 3 and name.lower() not in blocked and name.lower() not in seen:
                seen.add(name.lower())
                candidates_filtered.append(name)
    return candidates_filtered[:5]

def search_github_projects(query, top_n=3):
    """用 GitHub API 搜索项目"""
    url = f"{GITHUB_API}/search/repositories?q={urllib.parse.quote(query)}&sort=stars&per_page={top_n}"
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json", "User-Agent": "LinkArchivist/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return [{
                "name": repo["full_name"],
                "stars": repo["stargazers_count"],
                "description": repo.get("description", ""),
                "url": repo["html_url"],
                "updated": repo["updated_at"][:10],
                "language": repo.get("language", "N/A"),
            } for repo in data.get("items", [])[:top_n]]
    except Exception:
        return []

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "error": "Usage: github_discovery.py <text>"}))
        sys.exit(1)

    text = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    text = text[:5000]

    result = {
        "ok": True,
        "explicit_urls": find_github_urls(text),
        "suspected_names": extract_project_names(text),
    }

    searched = []
    for name in result["suspected_names"]:
        matches = search_github_projects(name)
        if matches:
            searched.append({"query": name, "matches": matches})

    result["search_results"] = searched
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
