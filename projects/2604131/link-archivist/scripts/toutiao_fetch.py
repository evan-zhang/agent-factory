#!/usr/bin/env python3
"""
toutiao_fetch.py - 今日头条文章内容提取

适用场景：今日头条移动端文章页 (m.toutiao.com)
原理：从 SSR HTML 的 RENDER_DATA JSON 中直接提取 articleInfo，跳过 JS 加密壳

使用方法：
    python3 toutiao_fetch.py <url>
    python3 toutiao_fetch.py "https://m.toutiao.com/i7633791560827683362/"

输出：JSON 格式的文章内容
"""

import sys
import json
import urllib.parse
import re
import argparse


def extract_render_data_from_html(html: str) -> dict:
    """从 SSR HTML 中提取 RENDER_DATA JSON"""
    start = html.find('RENDER_DATA')
    if start == -1:
        raise ValueError("页面中未找到 RENDER_DATA，可能是非SSR页面或已被拦截")

    start = html.find('>', start) + 1
    end = html.find('</script>', start)
    raw_data = html[start:end]

    # URL decode
    data = urllib.parse.unquote(raw_data)
    return json.loads(data)


def extract_article_info(render_data: dict) -> dict:
    """从 RENDER_DATA 中提取 articleInfo"""
    article_info = render_data.get('articleInfo', {})
    if not article_info:
        raise ValueError("RENDER_DATA 中未找到 articleInfo")

    seo_tdk = render_data.get('seoTDK', {})

    # 头条 API 结构变更：content 从 articleInfo.content 迁移到 articleInfo.thread.threadBase
    thread_base = article_info.get('thread', {}).get('threadBase', {})
    content_html = (
        thread_base.get('richContent', '') or
        thread_base.get('content', '') or
        article_info.get('content', '')
    )

    title = (
        thread_base.get('title', '') or
        article_info.get('title', '') or
        seo_tdk.get('title', '')
    )

    return {
        'title': title,
        'content': content_html,
        'publish_time': seo_tdk.get('publishTime', ''),
        'modified_time': seo_tdk.get('modifiedTime', ''),
        'abstract': seo_tdk.get('abstract', ''),
        'keywords': seo_tdk.get('keywords', ''),
        'detail_source': article_info.get('detailSource', ''),
        'media_user': article_info.get('mediaUser', {}),
        'url': article_info.get('url', ''),
        'is_original': article_info.get('isOriginal', False),
        'impression_count': article_info.get('impressionCount', 0),
    }


def clean_html_content(html_content: str) -> str:
    """把 articleInfo.content 的 HTML 片段转成纯文本"""
    import re
    # 去除 data-track 属性
    html_content = re.sub(r'\s*data-track="[^"]*"', '', html_content)
    # 简单的 HTML tag 去除
    text = re.sub(r'<[^>]+>', '', html_content)
    # 合并空白
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text.strip()


def fetch_article(url: str, timeout: int = 15) -> dict:
    """抓取头条文章"""
    import urllib.request

    if 'm.toutiao.com' not in url and 'toutiao.com' not in url:
        raise ValueError(f"不是头条文章URL: {url}")

    # 移动端 UA
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        html = resp.read().decode('utf-8', errors='replace')

    render_data = extract_render_data_from_html(html)
    article = extract_article_info(render_data)

    # 纯文本版本
    article['content_text'] = clean_html_content(article.get('content', ''))

    return {
        'success': True,
        'url': url,
        'data': article
    }


def main():
    parser = argparse.ArgumentParser(description='今日头条文章内容提取')
    parser.add_argument('url', help='头条文章URL')
    parser.add_argument('--text-only', action='store_true', help='只输出纯文本')
    parser.add_argument('--timeout', type=int, default=15, help='请求超时(秒)')
    args = parser.parse_args()

    try:
        result = fetch_article(args.url, timeout=args.timeout)
        data = result['data']

        if args.text_only:
            # short mode: 标题 + 前500字摘要
            print(f"# {data['title']}")
            print(f"来源: {data['detail_source']} | 发布时间: {data['publish_time']}")
            print()
            print(data['content_text'][:500])
            if len(data['content_text']) > 500:
                print(f"\n... [{len(data['content_text']) - 500} 字省略]")
        else:
            # full mode: 输出结构化 JSON
            print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({
            'success': False,
            'url': args.url,
            'error': str(e)
        }, ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()
