#!/usr/bin/env python3
"""
bp-prototype 模板生成脚本

功能：从 BP 规范和真实案例逆向生成四套空白母版模板
用法：python3 scripts/generate.py [--status] [--update-spec]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 路径配置
SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
REFERENCES_DIR = SKILL_DIR / "references"
VERSIONS_DIR = SKILL_DIR / "versions"
BP_SPEC_DIR = REFERENCES_DIR / "bp-spec"
BP_EXAMPLES_DIR = REFERENCES_DIR / "bp-examples"
TEMPLATE_RULES_DIR = REFERENCES_DIR / "template-rules"


def get_latest_version() -> str:
    """获取当前最新版本号"""
    if not VERSIONS_DIR.exists():
        return "v0.0"
    
    versions = []
    for d in VERSIONS_DIR.iterdir():
        if d.is_dir():
            # 从目录名解析版本，如 20260401-120000-v1
            parts = d.name.split("-")
            if len(parts) >= 3:
                ver = parts[-1]  # 最后一段是版本号
                if ver.startswith("v"):
                    versions.append(ver)
    
    if not versions:
        return "v0.0"
    
    # 解析版本号并排序
    def ver_key(v):
        num = int(v[1:])
        return num
    
    versions.sort(key=ver_key, reverse=True)
    return versions[0]


def get_next_version():
    """计算下一版本号"""
    latest = get_latest_version()
    # 处理 v0.0 或 v0 格式
    clean = latest.lstrip("v").split(".")[0]
    num = int(clean) + 1
    return f"v{num}"


def check_status():
    """查看当前状态"""
    print("=" * 50)
    print("bp-prototype 当前状态")
    print("=" * 50)
    
    # 最新版本
    latest = get_latest_version()
    print(f"\n最新版本：{latest}")
    
    # references 状态
    print("\n--- references/ ---")
    
    spec_file = BP_SPEC_DIR / "BP系统操作手册.md"
    if spec_file.exists():
        mtime = datetime.fromtimestamp(spec_file.stat().st_mtime)
        print(f"BP系统操作手册.md  ({mtime.strftime('%Y-%m-%d %H:%M')})")
    else:
        print("BP系统操作手册.md  ❌ 不存在（需从 GitHub 拉取）")
    
    # 模板示例
    templates = ["月报", "季报", "半年报", "年报"]
    for t in templates:
        f = BP_EXAMPLES_DIR / f"模板_v1_{t}.md"
        if f.exists():
            print(f"模板_v1_{t}.md  ✅")
        else:
            print(f"模板_v1_{t}.md  ❌")
    
    # 历史版本
    print("\n--- versions/ 历史版本 ---")
    if VERSIONS_DIR.exists():
        dirs = sorted([d for d in VERSIONS_DIR.iterdir() if d.is_dir()], reverse=True)
        for d in dirs[:5]:
            print(f"  {d.name}/")
        if len(dirs) > 5:
            print(f"  ... 还有 {len(dirs)-5} 个版本")
    else:
        print("  无历史版本")
    
    print()


def update_spec():
    """从 GitHub 更新 BP 系统操作手册"""
    import urllib.request
    import urllib.error
    
    url = "https://raw.githubusercontent.com/xgjk/dev-guide/main/02.%E4%BA%A7%E5%93%81%E4%B8%9A%E5%8A%A1AI%E6%96%87%E6%A1%A3/BP/BP%E7%B3%BB%E7%BB%9F%E4%B8%9A%E5%8A%A1%E8%AF%B4%E6%98%8E.md"
    dest = BP_SPEC_DIR / "BP系统操作手册.md"
    
    print(f"正在从 GitHub 拉取 BP系统操作手册...")
    print(f"URL: {url}")
    
    try:
        # 设置代理（如果有的话）
        proxies = {}
        import os
        http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
        https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        if http_proxy or https_proxy:
            proxies = {
                "http": http_proxy,
                "https": https_proxy,
            }
        
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        if proxies:
            handler = urllib.request.ProxyHandler(proxies)
            opener = urllib.request.build_opener(handler)
            response = opener.open(req, timeout=30)
        else:
            response = urllib.request.urlopen(req, timeout=30)
        
        content = response.read().decode("utf-8")
        
        # 写入文件
        BP_SPEC_DIR.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)
        
        lines = len(content.split("\n"))
        print(f"✅ 更新成功！写入 {lines} 行 → {dest}")
        
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP 错误：{e.code} {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 拉取失败：{e}")
        sys.exit(1)


def generate_templates():
    """生成四套模板（由 AI 推理完成，此处输出引导信息）"""
    next_ver = get_next_version()
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    version_dir = VERSIONS_DIR / f"{ts}-{next_ver}"
    
    print("=" * 50)
    print(f"bp-prototype 模板生成")
    print("=" * 50)
    print(f"版本：{next_ver}")
    print(f"输出目录：{version_dir}")
    print()
    
    # 检查必要的 references
    spec_file = BP_SPEC_DIR / "BP系统操作手册.md"
    if not spec_file.exists():
        print("❌ BP系统操作手册.md 不存在！")
        print("请先运行：python3 scripts/generate.py --update-spec")
        sys.exit(1)
    
    rules_file = TEMPLATE_RULES_DIR / "生成规则.md"
    if not rules_file.exists():
        print("❌ 生成规则.md 不存在！")
        sys.exit(1)
    
    print("✅ references/ 检查通过")
    print()
    print("AI 将根据以下素材逆向推理生成四套模板：")
    print("  1. BP系统操作手册.md（规范定义）")
    print("  2. 生成规则.md（映射逻辑）")
    print("  3. 集团BP/中心BP 示例（真实数据）")
    print("  4. 四套模板参考（现有模板）")
    print()
    print("生成说明：")
    print("  本脚本仅负责版本管理和文件写入。")
    print("  实际模板内容由 AI 阅读上述素材后推理生成。")
    print("  AI 需遵循 生成规则.md 中的章节映射和时间维度规则。")
    print()
    
    # 创建版本目录
    version_dir.mkdir(parents=True, exist_ok=True)
    
    # 输出文件路径（供 AI 后续写入）
    output_files = {
        "month": version_dir / f"P001-T001-MONTH-TPL-{next_ver}_月报模板.md",
        "quarter": version_dir / f"P001-T001-QUARTER-TPL-{next_ver}_季报模板.md",
        "halfyear": version_dir / f"P001-T001-HALFYEAR-TPL-{next_ver}_半年报模板.md",
        "year": version_dir / f"P001-T001-YEAR-TPL-{next_ver}_年报模板.md",
    }
    
    print("AI 需要生成的文件：")
    for name, path in output_files.items():
        print(f"  - {path.name}")
    print()
    
    # 返回供 AI 写入
    return next_ver, version_dir, output_files


def main():
    parser = argparse.ArgumentParser(description="bp-prototype 模板生成工具")
    parser.add_argument("--status", action="store_true", help="查看当前状态")
    parser.add_argument("--update-spec", action="store_true", help="从 GitHub 更新 BP 系统操作手册")
    parser.add_argument("--generate", action="store_true", help="执行模板生成")
    
    args = parser.parse_args()
    
    if args.status:
        check_status()
    elif args.update_spec:
        update_spec()
    elif args.generate:
        generate_templates()
    else:
        # 默认显示状态
        check_status()
        print("用法：")
        print("  python3 scripts/generate.py --status        # 查看状态")
        print("  python3 scripts/generate.py --update-spec   # 更新 BP 规范文档")
        print("  python3 scripts/generate.py --generate      # 生成模板（由 AI 执行）")


if __name__ == "__main__":
    main()
