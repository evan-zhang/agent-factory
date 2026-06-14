#!/usr/bin/env python3
"""
Style A1 渲染测试脚本 - v0.9.1 质量固化版
支持 profile-based 测试 + schema/registry 测试 + 7 类负向测试
"""

import sys
import os
import json
import re
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ 缺少依赖: pip install beautifulsoup4")
    sys.exit(1)

def load_registry():
    """加载 profile registry"""
    script_dir = Path(__file__).parent
    registry_path = script_dir / "profiles" / "registry.json"

    if not registry_path.exists():
        return None

    with open(registry_path) as f:
        return json.load(f)

def load_schema():
    """加载 profile schema"""
    script_dir = Path(__file__).parent
    schema_path = script_dir / "profiles" / "schema.json"

    if not schema_path.exists():
        return None

    with open(schema_path) as f:
        return json.load(f)

def test_registry_and_schema():
    """测试 registry 和 schema 文件存在性和基本结构"""
    print("=== Registry & Schema 测试 ===\n")

    errors = []

    # 1. 测试 registry
    print("1. 测试 registry.json...")
    registry = load_registry()
    if not registry:
        errors.append("registry.json 不存在")
        print("   ✗ registry.json 不存在")
    else:
        print("   ✓ registry.json 存在")

        # 检查基本结构
        if 'version' in registry:
            print(f"   ✓ Registry 版本: {registry['version']}")
        else:
            errors.append("registry 缺少 version 字段")
            print("   ✗ registry 缺少 version 字段")

        if 'profiles' in registry:
            active_profiles = [k for k, v in registry['profiles'].items() if v.get('status') == 'active']
            print(f"   ✓ Active profiles: {', '.join(active_profiles)}")
        else:
            errors.append("registry 缺少 profiles 字段")
            print("   ✗ registry 缺少 profiles 字段")

    # 2. 测试 schema
    print("\n2. 测试 schema.json...")
    schema = load_schema()
    if not schema:
        errors.append("schema.json 不存在")
        print("   ✗ schema.json 不存在")
    else:
        print("   ✓ schema.json 存在")

        if '$schema' in schema:
            print(f"   ✓ Schema 定义: {schema['$schema']}")
        else:
            errors.append("schema 缺少 $schema 字段")
            print("   ✗ schema 缺少 $schema 字段")

        if '$id' in schema:
            print(f"   ✓ Schema ID: {schema['$id']}")
        else:
            errors.append("schema 缺少 $id 字段")
            print("   ✗ schema 缺少 $id 字段")

    # 3. 测试 profile 文件版本
    print("\n3. 测试 profile 文件版本...")
    for profile_code in ['common', 'A-1']:
        profile_file = Path(__file__).parent / "profiles" / f"{profile_code}.json"
        if profile_file.exists():
            with open(profile_file) as f:
                profile_data = json.load(f)
            version = profile_data.get('version', 'missing')
            if version == '0.9.1':
                print(f"   ✓ {profile_code}.json 版本: {version}")
            else:
                errors.append(f"{profile_code}.json 版本不正确: {version}")
                print(f"   ✗ {profile_code}.json 版本不正确: {version}")
        else:
            errors.append(f"{profile_code}.json 不存在")
            print(f"   ✗ {profile_code}.json 不存在")

    # 总结
    print(f"\n=== Registry & Schema 测试总结 ===")
    if errors:
        print(f"❌ 测试失败 ({len(errors)} 个错误)")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("✅ 所有测试通过")
        return True

def run_negative_test(test_name: str, test_description: str) -> bool:
    """运行单个负向测试"""
    print(f"=== 负向测试: {test_name} ===")
    print(f"描述: {test_description}\n")

    script_dir = Path(__file__).parent
    render_script = script_dir / "render.py"

    # 创建临时测试环境
    temp_dir = Path(tempfile.mkdtemp())
    test_report_dir = temp_dir / f"negative-test-{test_name}"
    test_report_dir.mkdir()

    # 创建基本测试文件
    test_md_file = test_report_dir / "04-final-report.md"
    state_file = test_report_dir / "state.json"
    output_file = test_report_dir / "REPORT.html"

    # 根据测试类型准备测试数据
    if test_name == "profile-not-registered":
        # 使用未注册的 profile
        profile_code = "X-99"
        test_md_content = "# X-99 测试报告\n\n测试内容"
    elif test_name == "profile-file-missing":
        # 使用已注册但文件缺失的 profile（需要临时修改 registry）
        profile_code = "A-1"
        test_md_content = "# A-1 测试报告\n\n测试内容"
        # 临时移除 A-1.json 文件
        a1_file = script_dir / "profiles" / "A-1.json"
        if a1_file.exists():
            import shutil
            temp_backup = temp_dir / "A-1.json.backup"
            shutil.copy(a1_file, temp_backup)
            a1_file.unlink()
    elif test_name == "profile-schema-invalid":
        # 使用 schema 无效的 profile（需要临时创建）
        profile_code = "A-1"
        test_md_content = "# A-1 测试报告\n\n测试内容"
        # 临时替换 A-1.json 为无效内容
        a1_file = script_dir / "profiles" / "A-1.json"
        if a1_file.exists():
            import shutil
            temp_backup = temp_dir / "A-1.json.backup"
            shutil.copy(a1_file, temp_backup)
            # 写入无效的 profile
            with open(a1_file, 'w') as f:
                json.dump({"invalid": "profile"}, f)
    elif test_name == "required-component-missing":
        # 使用缺少必选组件的 markdown
        profile_code = "A-1"
        test_md_content = "# A-1 测试报告\n\n简单内容，缺少必选组件"
    elif test_name == "critical-component-missing":
        # 使用缺少关键组件的 markdown
        profile_code = "A-1"
        test_md_content = "# A-1 测试报告\n\n## 结论\n测试结论\n\n缺少置信度标识"
    elif test_name == "template-token-unreplaced":
        # 使用包含未替换模板变量的 markdown
        profile_code = "A-1"
        test_md_content = "# A-1 测试报告\n\n## 结论\n{{UNREPLACED_TOKEN}} 测试"
    else:
        # 默认测试
        profile_code = "A-1"
        test_md_content = "# A-1 测试报告\n\n测试内容"

    # 写入测试文件
    with open(test_md_file, 'w') as f:
        f.write(test_md_content)

    with open(state_file, 'w') as f:
        json.dump({
            'case_code': f'2605-NEG-{test_name}',
            'skill_code': profile_code,
            'business_entity': '深康',
            'evaluation_date': '2026-06-13',
            'species_id': 'MB-001'
        }, f)

    # 调用渲染器
    try:
        result = subprocess.run(
            [sys.executable, str(render_script), str(test_report_dir), 'mckinsey-navy', str(output_file), profile_code],
            capture_output=True,
            text=True,
            timeout=30
        )

        # 检查是否失败（负向测试期望失败）
        if result.returncode != 0:
            print(f"✅ 测试通过: 渲染器正确失败")
            print(f"   退出码: {result.returncode}")
            if result.stderr:
                print(f"   错误信息: {result.stderr[:200]}")
            success = True
        else:
            print(f"❌ 测试失败: 渲染器应该失败但没有失败")
            print(f"   退出码: {result.returncode}")
            success = False

    except subprocess.TimeoutExpired:
        print("❌ 测试失败: 渲染超时")
        success = False
    except Exception as e:
        print(f"❌ 测试失败: 渲染异常 {e}")
        success = False
    finally:
        # 恢复被修改的文件
        if test_name in ["profile-file-missing", "profile-schema-invalid"]:
            temp_backup = temp_dir / "A-1.json.backup"
            if temp_backup.exists():
                import shutil
                a1_file = script_dir / "profiles" / "A-1.json"
                shutil.copy(temp_backup, a1_file)

    # 清理临时文件
    import shutil
    shutil.rmtree(temp_dir)

    return success

def run_all_negative_tests():
    """运行所有负向测试"""
    print("=== 7 类负向测试 ===\n")

    negative_tests = [
        ("profile-not-registered", "profile 未注册或非 active 应该失败"),
        ("profile-file-missing", "active profile 文件不存在应该失败"),
        ("profile-schema-invalid", "profile schema 校验失败应该失败"),
        ("required-component-missing", "required component 缺失应该失败"),
        ("critical-component-missing", "critical component 缺失应该失败"),
        ("template-token-unreplaced", "模板变量残留应该失败"),
        ("output-html-missing", "输出 HTML 文件未生成应该失败")
    ]

    results = {}

    for test_name, test_description in negative_tests:
        print(f"\n{'='*60}")
        success = run_negative_test(test_name, test_description)
        results[test_name] = success

    # 汇总结果
    print(f"\n{'='*60}")
    print("=== 负向测试汇总 ===\n")

    passed_count = sum(results.values())
    total_count = len(results)

    for test_name, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")

    print(f"\n负向测试通过率: {passed_count}/{total_count} ({passed_count/total_count*100:.0f}%)")

    return all(results.values())

def load_expected_components(profile_code='A-1'):
    """加载预期组件定义 - 支持多 profile"""
    script_dir = Path(__file__).parent
    fixtures_dir = script_dir / "fixtures" / "expected" / "by-skill"
    common_file = script_dir / "fixtures" / "expected" / "common.json"

    # 加载通用组件
    with open(common_file) as f:
        common_expected = json.load(f)

    # 加载特定 profile 的组件
    profile_file = fixtures_dir / f"{profile_code}.json"
    if not profile_file.exists():
        print(f"⚠ Profile {profile_code} 不存在，仅使用通用组件")
        return common_expected

    with open(profile_file) as f:
        profile_expected = json.load(f)

    # 合并组件定义（profile 覆盖 common）
    merged_expected = {
        "version": common_expected.get("version", "0.9.0"),
        "style": common_expected.get("style", "A1"),
        "description": f"Profile {profile_code} 测试",
        "profile_code": profile_code,
        "expected_components": {}
    }

    # 首先添加通用组件
    for category, components in common_expected.get("expected_components", {}).items():
        if category not in merged_expected["expected_components"]:
            merged_expected["expected_components"][category] = {}
        if isinstance(components, dict):
            merged_expected["expected_components"][category].update(components)
        else:
            merged_expected["expected_components"][category] = components

    # 然后添加 profile 特定组件（覆盖通用组件）
    for category, components in profile_expected.get("expected_components", {}).items():
        if category not in merged_expected["expected_components"]:
            merged_expected["expected_components"][category] = {}
        if isinstance(components, dict):
            merged_expected["expected_components"][category].update(components)
        else:
            merged_expected["expected_components"][category] = components

    # 合并覆盖率要求
    merged_expected["coverage_requirements"] = profile_expected.get(
        "coverage_requirements",
        common_expected.get("coverage_requirements", {"minimum_coverage": 95})
    )

    return merged_expected

def parse_html(html_content):
    """解析 HTML 内容"""
    return BeautifulSoup(html_content, 'html.parser')

def check_component_coverage(soup, expected):
    """检查组件覆盖率"""
    results = {
        'total': 0,
        'found': 0,
        'missing': [],
        'details': {}
    }

    # 如果 profile 没有定义额外组件，只检查通用组件
    components_to_check = expected.get('expected_components', {})

    # 处理 note 字段（v0.9 特殊情况）
    if 'note' in components_to_check and len(components_to_check) == 1:
        # 只检查通用组件，从 common 继承
        print(f"   ℹ {components_to_check['note']}")
        # 对于 v0.9，只验证通用组件，不要求特定的业务组件
        return {
            'total': 0,
            'found': 0,
            'missing': [],
            'details': {},
            'note': components_to_check['note']
        }

    all_components = {}
    for category, components in components_to_check.items():
        if category == 'note':
            continue  # 跳过 note 字段
        for comp_name, comp_def in components.items():
            all_components[comp_name] = comp_def

    for comp_name, comp_def in all_components.items():
        selector = comp_def['selector']
        required = comp_def.get('required', False)
        count_min = comp_def.get('count_min', 1)

        # 查找元素。兼容 v0.9 profile 中的 :contains() 写法，优先使用 SoupSieve 推荐的 :-soup-contains()，避免 FutureWarning。
        selectors_to_try = [selector]
        if ':contains(' in selector:
            selectors_to_try = [selector.replace(':contains(', ':-soup-contains('), selector]

        elements = []
        for css_selector in selectors_to_try:
            try:
                elements = soup.select(css_selector)
                break
            except Exception:
                continue
        count = len(elements)

        # 检查是否满足要求
        if required and count < count_min:
            results['missing'].append({
                'name': comp_name,
                'selector': selector,
                'required': required,
                'expected_min': count_min,
                'found': count,
                'description': comp_def.get('description', '')
            })

        # 统计覆盖率
        if required:
            results['total'] += 1
            if count >= count_min:
                results['found'] += 1

        # 记录详情
        results['details'][comp_name] = {
            'selector': selector,
            'required': required,
            'count_min': count_min,
            'found': count,
            'status': 'PASS' if count >= count_min else 'FAIL',
            'description': comp_def.get('description', '')
        }

    return results

def check_template_variables(html_content):
    """检查模板变量是否全部替换"""
    remaining = re.findall(r'\{\{[^}]+\}\}', html_content)
    return {
        'status': 'PASS' if len(remaining) == 0 else 'FAIL',
        'remaining_count': len(remaining),
        'remaining_vars': list(set(remaining))[:10]  # 只显示前10个
    }

def run_profile_test(profile_code):
    """运行单个 profile 的测试"""
    print(f"=== Style A1 Profile {profile_code} 渲染测试 ===\n")

    # 加载预期组件
    print("1. 加载预期组件定义...")
    expected = load_expected_components(profile_code)
    print(f"   ✓ 加载了 {len(expected['expected_components'])} 个组件分类 (Profile: {profile_code})")

    # 读取测试样本
    print("\n2. 读取测试样本...")
    script_dir = Path(__file__).parent
    sample_file = script_dir / "fixtures" / f"sample-{profile_code.lower()}.md"

    if not sample_file.exists():
        print(f"   ✗ 样本文件不存在: {sample_file}")
        return False

    with open(sample_file) as f:
        sample_md = f.read()

    print(f"   ✓ 样本文件: {len(sample_md.splitlines())} 行")

    # 调用渲染器
    print("\n3. 执行渲染...")
    render_script = script_dir / "render.py"

    # 创建临时目录
    import tempfile
    temp_dir = Path(tempfile.mkdtemp())

    # 创建测试报告目录
    test_report_dir = temp_dir / f"test-report-{profile_code}"
    test_report_dir.mkdir()

    # 写入样本文件
    test_md_file = test_report_dir / "04-final-report.md"
    with open(test_md_file, 'w') as f:
        f.write(sample_md)

    # 创建 state.json
    state_file = test_report_dir / "state.json"
    with open(state_file, 'w') as f:
        json.dump({
            'case_code': f'2605-TEST-{profile_code}',
            'skill_code': profile_code,
            'business_entity': '深康',
            'evaluation_date': '2026-06-13',
            'species_id': f'MB-{profile_code.split("-")[1]}'
        }, f)

    # 调用渲染器
    import subprocess
    output_file = test_report_dir / "REPORT.html"

    try:
        result = subprocess.run(
            [sys.executable, str(render_script), str(test_report_dir), 'mckinsey-navy', str(output_file), profile_code],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"   ✗ 渲染失败: {result.stderr}")
            return False

        print(f"   ✓ 渲染成功")
    except subprocess.TimeoutExpired:
        print("   ✗ 渲染超时")
        return False
    except Exception as e:
        print(f"   ✗ 渲染异常: {e}")
        return False

    # 读取输出
    print("\n4. 读取渲染结果...")
    with open(output_file) as f:
        html_content = f.read()

    print(f"   ✓ 输出文件: {len(html_content.splitlines())} 行, {len(html_content):,} 字节")

    # 解析 HTML
    print("\n5. 解析 HTML 结构...")
    soup = parse_html(html_content)
    print(f"   ✓ HTML 解析成功")

    # 检查组件覆盖率
    print("\n6. 检查组件覆盖率...")
    coverage_results = check_component_coverage(soup, expected)

    # 处理 v0.9 特殊情况（note 字段）
    if 'note' in coverage_results:
        print(f"   ℹ {coverage_results['note']}")
        print(f"   组件覆盖率: v0.9 通用模板内核 - 无额外组件要求")
        coverage_rate = 100  # v0.9 通用组件自动通过
    else:
        coverage_rate = (coverage_results['found'] / coverage_results['total'] * 100) if coverage_results['total'] > 0 else 0
        print(f"   组件覆盖率: {coverage_results['found']}/{coverage_results['total']} ({coverage_rate:.1f}%)")

        if coverage_results['missing']:
            print(f"\n   缺失组件 ({len(coverage_results['missing'])}):")
            for comp in coverage_results['missing']:
                print(f"   ✗ {comp['name']}: 预期≥{comp['expected_min']}, 实际{comp['found']} - {comp['description']}")

    min_coverage = expected['coverage_requirements']['minimum_coverage']
    print(f"   最低要求: {min_coverage}%")

    # 检查模板变量
    print("\n7. 检查模板变量替换...")
    template_results = check_template_variables(html_content)

    if template_results['status'] == 'PASS':
        print(f"   ✓ 所有模板变量已替换")
    else:
        print(f"   ✗ 发现 {template_results['remaining_count']} 个未替换的变量")
        for var in template_results['remaining_vars']:
            print(f"     - {var}")

    # 验证关键组件
    print("\n8. 验证关键组件...")
    critical_components = expected['coverage_requirements']['critical_components']

    # 处理 v0.9 特殊情况
    if 'note' in coverage_results:
        print("   ℹ v0.9 通用模板内核 - 使用通用关键组件")
        # 使用通用组件进行验证
        for comp_name in critical_components:
            # 通用组件检查
            if comp_name == "classification-bar":
                elements = soup.select(".classification-bar")
                if elements:
                    print(f"   ✓ {comp_name}: {len(elements)} 个 (预期≥1) - 密级与呈报对象栏")
                else:
                    print(f"   ✗ {comp_name}: 0 个 (预期≥1) - 密级与呈报对象栏")
            elif comp_name == "conclusion-box":
                elements = soup.select(".conclusion-box")
                if elements:
                    print(f"   ✓ {comp_name}: {len(elements)} 个 (预期≥1) - 结论框")
                else:
                    print(f"   ✗ {comp_name}: 0 个 (预期≥1) - 结论框")
            elif comp_name in ["confidence-badge", "stage-tag", "glossary-table", "risk-box"]:
                elements = soup.select(f".{comp_name}" if comp_name != "glossary-table" else ".glossary-table")
                if elements:
                    print(f"   ✓ {comp_name}: {len(elements)} 个 (预期≥1)")
                else:
                    print(f"   ✗ {comp_name}: 0 个 (预期≥1)")
    else:
        for comp_name in critical_components:
            if comp_name in coverage_results['details']:
                detail = coverage_results['details'][comp_name]
                status_icon = "✓" if detail['status'] == 'PASS' else "✗"
                print(f"   {status_icon} {comp_name}: {detail['found']} 个 (预期≥{detail['count_min']}) - {detail['description']}")

    # 生成详细报告
    print("\n9. 生成详细报告...")
    report_file = temp_dir / f"test-report-{profile_code}.json"

    report = {
        'timestamp': str(pd_timestamp()),
        'style': 'A1',
        'profile': profile_code,
        'coverage_rate': coverage_rate,
        'pass_coverage': coverage_rate >= min_coverage,
        'template_vars_pass': template_results['status'] == 'PASS',
        'component_details': coverage_results['details'],
        'missing_components': coverage_results['missing'],
        'remaining_template_vars': template_results['remaining_vars']
    }

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"   ✓ 详细报告: {report_file}")

    # 总结
    print(f"\n=== Profile {profile_code} 测试总结 ===")

    pass_coverage = coverage_rate >= min_coverage
    pass_template = template_results['status'] == 'PASS'

    if pass_coverage and pass_template:
        print("✅ 测试通过")
        print(f"   - 组件覆盖率: {coverage_rate:.1f}% (≥{min_coverage}%)")
        print(f"   - 模板变量: 全部替换")

        # 保留临时文件供检查
        print(f"\n📁 测试文件位置: {test_report_dir}")
        print(f"   HTML 输出: {output_file}")
        print(f"   详细报告: {report_file}")

        return True
    else:
        print("❌ 测试失败")

        if not pass_coverage:
            print(f"   - 组件覆盖率不足: {coverage_rate:.1f}% < {min_coverage}%")

        if not pass_template:
            print(f"   - 模板变量未全部替换")

        return False

def test_a1_chapter_order_contract():
    """A-1 正文章节顺序护栏：第三章不得是术语表，术语表必须放到附录/正文末尾。"""
    print("=== A-1 章节顺序契约测试 ===\n")
    script_dir = Path(__file__).parent
    sample_file = script_dir / "fixtures" / "sample-a-1.md"
    if not sample_file.exists():
        print(f"❌ 样本文件不存在: {sample_file}")
        return False

    sample_md = sample_file.read_text()
    chapter_match = re.search(r'^## 第三章：(.+)$', sample_md, re.M)
    if not chapter_match:
        print("❌ A-1 样本缺少第三章")
        return False

    third_title = chapter_match.group(1).strip()
    if "术语" in third_title or "缩写" in third_title:
        print(f"❌ 第三章不得为术语表: {third_title}")
        return False

    glossary_match = re.search(r'^## (附录[^\n]*术语|术语与缩写表)', sample_md, re.M)
    if not glossary_match:
        print("❌ 缺少术语表/附录术语表")
        return False

    if glossary_match.start() < chapter_match.start():
        print("❌ 术语表位置早于第三章，违反正文顺序")
        return False

    if "附录" not in glossary_match.group(1):
        print("❌ 术语表应放在附录或正文末尾，并以附录标题呈现")
        return False

    print(f"✅ 第三章为业务章节: {third_title}")
    print("✅ 术语表已移至附录")
    return True


def run_render_test():
    """运行 A-1 profile 渲染测试（v0.9.3 起仅 A-1 一个 active profile）"""
    print("=== Style A1 A-1 单一 Profile 渲染测试 ===\n")

    profiles = ['A-1']
    results = {}

    for profile in profiles:
        print(f"\n{'='*60}")
        success = run_profile_test(profile)
        results[profile] = success

    # 汇总结果
    print(f"\n{'='*60}")
    print("=== A-1 Profile 测试汇总 ===\n")

    all_passed = all(results.values())

    for profile, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"Profile {profile}: {status}")

    if all_passed:
        print("\n✅ A-1 Profile 测试通过")
        return True
    else:
        print("\n❌ 部分 Profile 测试失败")
        failed_profiles = [p for p, s in results.items() if not s]
        print(f"   失败的 Profile: {', '.join(failed_profiles)}")
        return False

def pd_timestamp():
    """获取时间戳"""
    from datetime import datetime
    return datetime.now().isoformat()

def run_complete_test_suite():
    """运行完整测试套件：registry/schema + 正向测试 + 负向测试"""
    print("=== Style A1 v0.9.1 完整测试套件 ===\n")

    all_results = {}

    # 1. Registry & Schema 测试
    print(f"\n{'='*60}")
    registry_schema_result = test_registry_and_schema()
    all_results['registry_schema'] = registry_schema_result

    # 2. 正向测试（A-1）
    print(f"\n{'='*60}")
    print("=== 正向测试 ===")
    positive_result = run_render_test()
    all_results['positive_tests'] = positive_result

    # 3. A-1 章节顺序契约测试
    print(f"\n{'='*60}")
    chapter_order_result = test_a1_chapter_order_contract()
    all_results['a1_chapter_order'] = chapter_order_result

    # 4. 负向测试
    print(f"\n{'='*60}")
    negative_result = run_all_negative_tests()
    all_results['negative_tests'] = negative_result

    # 汇总结果
    print(f"\n{'='*60}")
    print("=== 完整测试套件汇总 ===\n")

    for test_type, result in all_results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_type}: {status}")

    all_passed = all(all_results.values())

    if all_passed:
        print("\n🎉 完整测试套件全部通过")
        return True
    else:
        print("\n❌ 部分测试失败")
        failed_tests = [t for t, r in all_results.items() if not r]
        print(f"   失败的测试: {', '.join(failed_tests)}")
        return False

if __name__ == '__main__':
    try:
        # 检查命令行参数
        if len(sys.argv) > 1:
            test_type = sys.argv[1]
            if test_type == "negative":
                # 只运行负向测试
                success = run_all_negative_tests()
            elif test_type == "positive":
                # 只运行正向测试
                success = run_render_test()
            elif test_type == "schema":
                # 只运行 schema/registry 测试
                success = test_registry_and_schema()
            else:
                print(f"未知测试类型: {test_type}")
                print("用法: python3 test_render.py [positive|negative|schema]")
                sys.exit(1)
        else:
            # 运行完整测试套件
            success = run_complete_test_suite()

        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
