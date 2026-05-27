#!/usr/bin/env python3
"""KB Graph 编译层：Markdown 解析 + LLM 语义编译"""
import hashlib
import json
import re
import sys
import time
from pathlib import Path

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_markdown(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    title = ""
    lines = content.split("\n")
    for line in lines:
        m = re.match(r"^#+\s+(.+)", line)
        if m:
            title = m.group(1).strip()
            break
    return {"title": title or Path(path).stem, "content": content}

def call_llm(content: str, title: str) -> dict:
    """
    调用 LLM 生成摘要/实体/标签/关系。
    顺序尝试：MiniMax-M2.7 → GLM-Z1-0528 → DeepSeek-V3
    返回结构化 dict，失败抛异常。
    """
    import os

    system_prompt = """你是一个知识库索引助手。请根据用户提供的文档内容，生成结构化的索引信息。

请严格按以下 JSON 格式输出，不要输出任何其他内容：

{
  "title": "文档标题（从内容中提取或使用给定标题）",
  "summary": "不超过200字的中文摘要，概括文档核心内容",
  "entities": ["实体1", "实体2", ...],
  "tags": ["标签1", "标签2", "标签3"],
  "relationships": [
    {"type": "reference", "target": "文档或文件名", "description": "引用关系描述"},
    {"type": "topic", "target": "主题或概念", "description": "主题关联描述"}
  ],
  "confidence": "high"
}

要求：
- summary 不超过200字
- entities 只列出文档中明确提到的关键概念、项目、人名、术语（最多10个）
- tags 从以下标签表中选择最相关的1-3个：AI, 架构, 安全, 运维, 产品, 运营, 前端, 后端, 数据库, 工具, 流程, 综合
- relationships 提取文档中的关系：
  * reference: 文件间引用（如：参考了、见、详见等）
  * topic: 主题关联（如：相关主题、属于、涉及等）
- confidence 表示你对摘要和实体提取的置信度：high/medium/low
- 如果文档内容不足以提取实体，entities 可以为空数组
- 如果没有明确的关系，relationships 可以为空数组"""

    # 模型候选列表
    models = [
        ("MiniMax", "MiniMax-M2.7-highspeed", os.environ.get("MINIMAX_API_KEY", "")),
        ("GLM", "GLM-Z1-0528", os.environ.get("ZHIPU_API_KEY", "")),
        ("DeepSeek", "deepseek-v4-flash", os.environ.get("DEEPSEEK_API_KEY", "")),
    ]

    # 构建 prompt，只取前 3000 字
    user_prompt = f"文档标题：{title}\n\n文档内容（前3000字）：\n{content[:3000]}"

    last_error = None

    for provider, model, api_key in models:
        if not api_key:
            continue

        try:
            if provider == "MiniMax":
                import openai
                client = openai.OpenAI(
                    api_key=api_key,
                    base_url="https://api.minimax.io/v1"
                )
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=1024,
                    temperature=0.3,
                )
                raw = response.choices[0].message.content

            elif provider == "GLM":
                import openai
                client = openai.OpenAI(
                    api_key=api_key,
                    base_url="https://open.bigmodel.cn/api/paas/v4"
                )
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=1024,
                    temperature=0.3,
                )
                raw = response.choices[0].message.content

            elif provider == "DeepSeek":
                import openai
                client = openai.OpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=1024,
                    temperature=0.3,
                    response_format={"type": "json_object"},
                )
                raw = response.choices[0].message.content

            # 解析 JSON
            result = json.loads(raw.strip())

            # 校验必要字段
            for field in ("summary", "entities", "tags"):
                if field not in result:
                    result[field] = [] if field in ("entities", "tags") else ""

            # 增强置信度计算：基于内容长度和 LLM 返回质量
            base_confidence = result.get("confidence", "medium")
            content_length_factor = min(len(content) / 1000, 1.0)  # 内容长度因子

            # 计算质量分数
            quality_score = 0
            if result.get("summary"):
                quality_score += 2
            if result.get("entities"):
                quality_score += 2
            if result.get("tags"):
                quality_score += 1
            if result.get("relationships"):
                quality_score += 2

            quality_factor = min(quality_score / 7, 1.0)  # 质量因子

            # 综合置信度计算
            confidence_map = {"high": 3, "medium": 2, "low": 1}
            base_score = confidence_map.get(base_confidence, 2)
            final_score = (base_score * 0.5 + content_length_factor * 2 + quality_factor * 2) / 4.5

            if final_score >= 2.5:
                final_confidence = "high"
            elif final_score >= 1.5:
                final_confidence = "medium"
            else:
                final_confidence = "low"

            return {
                "title": result.get("title", title),
                "summary": result.get("summary", "")[:300],
                "entities": list(result.get("entities", []))[:10],
                "tags": list(result.get("tags", []))[:3],
                "relationships": list(result.get("relationships", []))[:20],
                "confidence": final_confidence,
                "provider": provider,
                "model": model,
                "confidence_score": round(final_score, 2),
            }

        except Exception as e:
            last_error = f"{provider}: {e}"
            continue

    # 所有模型都失败
    raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")

def compile_with_llm(file_path, schema_path=None, test_mode=False):
    """对单个文件执行 LLM 编译，返回 entry dict。"""
    parsed = parse_markdown(file_path)

    if test_mode:
        # 测试模式：返回模拟数据
        return {
            "title": parsed["title"],
            "summary": f"测试模式：{parsed['content'][:100]}...",
            "entities": ["实体1", "实体2"],
            "tags": ["AI", "架构"],
            "relationships": [
                {"type": "topic", "target": "测试主题", "description": "测试模式下的主题关联"}
            ],
            "confidence": "medium",
            "provider": "test",
            "model": "test",
            "confidence_score": 1.5,
            "sha256": sha256(file_path),
        }

    result = call_llm(parsed["content"], parsed["title"])
    result["sha256"] = sha256(file_path)
    return result

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--schema", default=None)
    parser.add_argument("--embedding", action="store_true", help="同时生成语义向量")
    args = parser.parse_args()

    entry = compile_with_llm(args.file, args.schema)

    # 如果需要生成 embedding
    if args.embedding and not getattr(args, 'test_mode', False):
        try:
            from query import get_text_embedding
            text = f"{entry.get('title', '')} {entry.get('summary', '')}"
            embedding = get_text_embedding(text)
            entry["embedding"] = embedding
        except Exception as e:
            # embedding 生成失败不影响主流程
            print(f"Warning: Failed to generate embedding: {e}", file=sys.stderr)

    print(json.dumps({"ok": True, "entry": entry}))

if __name__ == "__main__":
    main()
