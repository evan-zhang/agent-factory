#!/usr/bin/env python3
"""Check-1: 验证失败文件数"""
import json
import sys

vault_path = "/Users/evan/Library/Mobile Documents/iCloud~md~obsidian/Documents/日常学习"
cache_file = f"{vault_path}/.kb-workdir/kb_cache.json"

try:
    with open(cache_file) as f:
        cache = json.load(f)
    
    failed_count = sum(1 for v in cache.values() if v.get('status') == 'failed')
    
    # 输出纯数字，不包含任何其他文本
    print(failed_count)
    
    sys.exit(0 if failed_count == 0 else 1)
    
except Exception as e:
    print(f"错误: {e}")
    sys.exit(1)
