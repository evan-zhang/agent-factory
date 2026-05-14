#!/usr/bin/env python3
"""rewrite.py — 口播稿预处理（文本分段、字数统计、风格判断）

这个脚本主要做文本预处理工作：
- 分段优化
- 字数统计
- 内容类型/风格判断
- 输出预处理后的文本

实际的口播稿改写由 Agent 运行时用大模型完成。
此脚本为 Agent 提供辅助信息，也可在独立运行时通过改写 prompt 模板指导改写。

用法: python3 rewrite.py <input_text> <output_text> <target_minutes> <target_chars> <style>
"""
import sys
import json
import re
import os

# 风格关键词映射
STYLE_KEYWORDS = {
    "讲解风": ["教程", "指南", "how to", "步骤", "原理", "技术", "配置", "安装", "部署",
              "api", "sdk", "代码", "算法", "架构", "实现", "开发", "编程", "debug"],
    "播报风": ["新闻", "快讯", "报道", "公告", "发布", "更新", "通知", "消息", "动态",
              "事件", "突发", "最新"],
    "叙事风": ["故事", "小说", "传说", "经历", "回忆", "旅途", "冒险", "第一章",
              "Chapter", "从前", "很久以前", "那天"],
    "专业风": ["报告", "分析", "数据", "市场", "营收", "利润", "增长", "战略",
              "规划", "指标", "OKR", "KPI", "预算", "财报", "季度"],
    "轻松风": ["分享", "推荐", "好物", "生活", "旅行", "美食", "日常", "想法",
              "感慨", "随笔", "闲聊", "今天"],
}


def detect_style(text):
    """根据内容关键词判断口播风格"""
    text_lower = text[:2000].lower()  # 只取前 2000 字判断
    scores = {}
    for style, keywords in STYLE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        scores[style] = score
    
    # 返回得分最高的风格
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "讲解风"  # 默认风格
    return best


def split_paragraphs(text, max_chars=1024):
    """将文本按段落分割，确保每段不超过 max_chars"""
    paragraphs = text.split("\n\n")
    result = []
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) <= max_chars:
            result.append(para)
        else:
            # 按句子分割长段落
            sentences = re.split(r'(?<=[。！？；\n])', para)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) > max_chars and current:
                    result.append(current.strip())
                    current = sent
                else:
                    current += sent
            if current.strip():
                result.append(current.strip())
    
    return result


def estimate_duration(char_count, speed=250):
    """估算口播时长（分钟）"""
    return char_count / speed


def preprocess(input_path, output_path, target_minutes, target_chars, style):
    """主预处理流程"""
    with open(input_path, "r", encoding="utf-8") as f:
        text = f.read()
    
    # 统计
    char_count = len(text)
    paragraphs = split_paragraphs(text)
    
    # 风格判断
    if style == "auto" or not style:
        detected_style = detect_style(text)
    else:
        detected_style = style
    
    # 风格→音色映射
    voice_map = {
        "讲解风": "Chinese (Mandarin)_Male_Announcer",
        "播报风": "Chinese (Mandarin)_News_Anchor",
        "叙事风": "Chinese (Mandarin)_Warm_Girl",
        "专业风": "Chinese (Mandarin)_Reliable_Executive",
        "轻松风": "Chinese (Mandarin)_Sweet_Lady",
    }
    voice_id = voice_map.get(detected_style, "Chinese (Mandarin)_Male_Announcer")
    
    # 预处理输出（包含元信息头）
    meta = {
        "char_count": char_count,
        "paragraph_count": len(paragraphs),
        "detected_style": detected_style,
        "voice_id": voice_id,
        "target_minutes": target_minutes,
        "target_chars": target_chars,
        "estimated_original_duration": round(estimate_duration(char_count), 1),
    }
    
    # 输出预处理后的文本（带元信息头）
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"<!-- file2voice-meta: {json.dumps(meta, ensure_ascii=False)} -->\n")
        f.write(f"<!-- 自动检测风格: {detected_style} -->\n")
        f.write(f"<!-- 建议音色: {voice_id} -->\n")
        f.write(f"<!-- 目标: {target_minutes}分钟 / {target_chars}字 -->\n")
        f.write("\n")
        f.write(text)
    
    # 输出 JSON 元信息到 stderr（供脚本调用者使用）
    meta_json = json.dumps(meta, ensure_ascii=False)
    print(meta_json, file=sys.stderr)
    
    return meta


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 rewrite.py <input> <output> [target_minutes] [target_chars] [style]", file=sys.stderr)
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    target_minutes = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    target_chars = int(sys.argv[4]) if len(sys.argv) > 4 else 1250
    style = sys.argv[5] if len(sys.argv) > 5 else "auto"
    
    meta = preprocess(input_path, output_path, target_minutes, target_chars, style)
    print(f"[rewrite] 预处理完成: {meta['char_count']}字, 风格={meta['detected_style']}, 音色={meta['voice_id']}", file=sys.stderr)
