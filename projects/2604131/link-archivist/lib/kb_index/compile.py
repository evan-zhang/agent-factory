#!/usr/bin/env python3
"""
Compile layer: LLM-based semantic extraction (for force-rebuild only).

This module uses LLM to extract summary/entities/tags from Markdown content.
It's ONLY used when --force-llm flag is set; main path uses frontmatter.
"""
import hashlib
import json
import re
from pathlib import Path
from typing import Dict, Any


def sha256(path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_markdown(path: Path) -> Dict[str, str]:
    """Extract title and content from Markdown.

    Args:
        path: Path to Markdown file

    Returns:
        Dict with title and content
    """
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


def call_llm(content: str, title: str) -> Dict[str, Any]:
    """Call LLM to generate structured metadata.

    Args:
        content: Document content
        title: Document title

    Returns:
        Structured dict with summary, entities, tags, relationships, confidence

    Raises:
        RuntimeError: If all LLM providers fail
    """
    import os

    system_prompt = """You are a knowledge base indexing assistant. Generate structured index information based on the provided document content.

Please output strictly in the following JSON format, without any other content:

{
  "title": "Document title (extracted from content or use given title)",
  "summary": "Chinese summary no more than 200 characters, summarizing core content",
  "entities": ["entity1", "entity2", ...],
  "tags": ["tag1", "tag2", "tag3"],
  "relationships": [
    {"type": "reference", "target": "document or file name", "description": "reference description"},
    {"type": "topic", "target": "topic or concept", "description": "topic association description"}
  ],
  "confidence": "high"
}

Requirements:
- summary: no more than 200 characters
- entities: list key concepts, projects, people, terms explicitly mentioned (max 10)
- tags: select 1-3 most relevant from: AI, 架构, 安全, 运维, 产品, 运营, 前端, 后端, 数据库, 工具, 流程, 综合
- relationships: extract document relationships:
  * reference: file references (e.g., referenced, see, refer to)
  * topic: topic associations (e.g., related topic, belongs to, involves)
- confidence: your confidence in summary and entity extraction: high/medium/low
- entities can be empty array if content insufficient
- relationships can be empty array if no clear relationships"""

    # Model candidates
    models = [
        ("MiniMax", "MiniMax-M2.7-highspeed", os.environ.get("MINIMAX_API_KEY", "")),
        ("GLM", "GLM-Z1-0528", os.environ.get("ZHIPU_API_KEY", "")),
        ("DeepSeek", "deepseek-v4-flash", os.environ.get("DEEPSEEK_API_KEY", "")),
    ]

    # Build prompt, only first 3000 characters
    user_prompt = f"Document title: {title}\n\nDocument content (first 3000 chars):\n{content[:3000]}"

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

            # Parse JSON
            result = json.loads(raw.strip())

            # Validate required fields
            for field in ("summary", "entities", "tags"):
                if field not in result:
                    result[field] = [] if field in ("entities", "tags") else ""

            # Enhanced confidence calculation
            base_confidence = result.get("confidence", "medium")
            content_length_factor = min(len(content) / 1000, 1.0)

            # Calculate quality score
            quality_score = 0
            if result.get("summary"):
                quality_score += 2
            if result.get("entities"):
                quality_score += 2
            if result.get("tags"):
                quality_score += 1
            if result.get("relationships"):
                quality_score += 2

            quality_factor = min(quality_score / 7, 1.0)

            # Comprehensive confidence calculation
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

    # All models failed
    raise RuntimeError(f"All LLM providers failed. Last error: {last_error}")


def compile_with_llm(
    file_path: Path,
    schema_path: Path = None,
    test_mode: bool = False
) -> Dict[str, Any]:
    """Compile single file with LLM.

    Args:
        file_path: Path to Markdown file
        schema_path: Optional schema path (not used)
        test_mode: If true, return mock data

    Returns:
        Entry dict with compiled metadata
    """
    parsed = parse_markdown(file_path)

    if test_mode:
        # Test mode: return mock data
        return {
            "title": parsed["title"],
            "summary": f"Test mode: {parsed['content'][:100]}...",
            "entities": ["entity1", "entity2"],
            "tags": ["AI", "架构"],
            "relationships": [
                {"type": "topic", "target": "test topic", "description": "topic association in test mode"}
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
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="KB Index LLM compile")
    parser.add_argument("--file", required=True, help="Markdown file path")
    parser.add_argument("--schema", help="Schema path (not used)")
    parser.add_argument("--test-mode", action="store_true", help="Test mode with mock data")
    args = parser.parse_args()

    try:
        entry = compile_with_llm(
            Path(args.file),
            Path(args.schema) if args.schema else None,
            args.test_mode
        )
        print(json.dumps({"ok": True, "entry": entry}, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
