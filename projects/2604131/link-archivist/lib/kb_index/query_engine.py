#!/usr/bin/env python3
"""
Query engine: keyword / semantic / hybrid search modes.

This module provides search capabilities over the indexed entries.
Default mode is keyword (no external dependencies).
"""
import json
from pathlib import Path
from typing import Dict, Any, List


def load_entries(root: Path) -> Dict[str, Any]:
    """Load entries from .kb-workdir/entries.json."""
    entries_path = Path(root) / ".kb-workdir" / "entries.json"
    if not entries_path.exists():
        return {}
    try:
        return json.loads(entries_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def search_by_keyword(root: Path, query_str: str) -> List[Dict[str, Any]]:
    """Keyword search: title / summary / tags / entities.

    Args:
        root: Knowledge base root directory
        query_str: Query string

    Returns:
        List of results with score, entry, and rel_path
    """
    entries = load_entries(root)
    results = []
    q = query_str.lower()

    for rel_path, entry in entries.items():
        title = entry.get("title", "").lower()
        summary = entry.get("summary", "").lower()
        tags = " ".join([t.lower() for t in entry.get("tags", [])])
        entities = " ".join([e.lower() for e in entry.get("entities", [])])

        score = 0
        matched_fields = []

        if q in title:
            score += 10
            matched_fields.append("title")
        if q in summary:
            score += 5
            matched_fields.append("summary")
        if q in tags:
            score += 3
            matched_fields.append("tags")
        if q in entities:
            score += 3
            matched_fields.append("entities")

        if score > 0:
            results.append({
                "score": score,
                "entry": entry,
                "rel_path": rel_path,
                "matched_fields": matched_fields,
            })

    # Sort by score descending
    results.sort(key=lambda x: -x["score"])
    return results[:10]


def search_by_semantic(root: Path, query_str: str) -> List[Dict[str, Any]]:
    """Semantic search using vector embeddings.

    Args:
        root: Knowledge base root directory
        query_str: Query string

    Returns:
        List of results with similarity score

    Note:
        Requires OPENAI_API_KEY and embeddings.json to exist.
        Falls back to empty list if unavailable.
    """
    entries = load_entries(root)
    embeddings_path = Path(root) / ".kb-workdir" / "embeddings.json"

    if not embeddings_path.exists():
        return []

    try:
        embeddings = json.loads(embeddings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    # Generate query embedding
    try:
        query_embedding = get_text_embedding(query_str)
    except RuntimeError:
        return []

    # Calculate similarities
    results = []
    for rel_path, embedding in embeddings.items():
        if rel_path in entries:
            similarity = cosine_similarity(query_embedding, embedding)
            if similarity > 0:
                results.append({
                    "score": similarity,
                    "entry": entries[rel_path],
                    "rel_path": rel_path,
                })

    results.sort(key=lambda x: -x["score"])
    return results[:10]


def get_text_embedding(text: str) -> List[float]:
    """Generate text embedding using OpenAI API.

    Args:
        text: Input text

    Returns:
        Embedding vector

    Raises:
        RuntimeError: If API key missing or call fails
    """
    import os

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in environment")

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            input=text[:8191],  # OpenAI limit
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"Failed to generate embedding: {e}")


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    try:
        import numpy as np
    except ImportError:
        # Fallback to pure Python
        def dot(v1, v2):
            return sum(a * b for a, b in zip(v1, v2))

        def norm(v):
            return sum(x * x for x in v) ** 0.5

        dot_product = dot(vec1, vec2)
        norm1 = norm(vec1)
        norm2 = norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0
        return dot_product / (norm1 * norm2)

    # NumPy version
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)

    if norm1 == 0 or norm2 == 0:
        return 0
    return dot_product / (norm1 * norm2)


def search_by_hybrid(root: Path, query_str: str) -> List[Dict[str, Any]]:
    """Hybrid search: fusion of keyword and semantic results.

    Args:
        root: Knowledge base root directory
        query_str: Query string

    Returns:
        List of results with combined scores
    """
    keyword_results = search_by_keyword(root, query_str)
    semantic_results = search_by_semantic(root, query_str)

    # Combine results, avoiding duplicates
    combined = {}

    for r in keyword_results:
        path = r["rel_path"]
        combined[path] = {
            "score": r["score"],
            "entry": r["entry"],
            "rel_path": path,
            "keyword_score": r["score"],
            "semantic_score": 0,
            "matched_fields": r.get("matched_fields", []),
        }

    for r in semantic_results:
        path = r["rel_path"]
        if path in combined:
            combined[path]["semantic_score"] = r["score"]
            # Weighted fusion: 60% keyword, 40% semantic
            combined[path]["score"] = combined[path]["keyword_score"] * 0.6 + r["score"] * 0.4
        else:
            combined[path] = {
                "score": r["score"] * 0.4,  # Downweight if only semantic
                "entry": r["entry"],
                "rel_path": path,
                "keyword_score": 0,
                "semantic_score": r["score"],
                "matched_fields": [],
            }

    # Sort and return top 10
    results = sorted(combined.values(), key=lambda x: -x["score"])[:10]
    return results


def query(
    query_str: str,
    root: Path,
    mode: str = "keyword"
) -> Dict[str, Any]:
    """Main query entry point.

    Args:
        query_str: Query string
        root: Knowledge base root directory
        mode: Query mode (keyword/semantic/hybrid)

    Returns:
        Result dict with ok, results, stats, method, query, total
    """
    if mode == "keyword":
        results = search_by_keyword(root, query_str)
    elif mode == "semantic":
        results = search_by_semantic(root, query_str)
    elif mode == "hybrid":
        results = search_by_hybrid(root, query_str)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    return {
        "ok": True,
        "results": [r["entry"] for r in results],
        "stats": [
            {
                "path": r["rel_path"],
                "score": round(r["score"], 4),
                "keyword_score": round(r.get("keyword_score", 0), 4),
                "semantic_score": round(r.get("semantic_score", 0), 4),
                "matched_fields": r.get("matched_fields", []),
            }
            for r in results
        ],
        "method": mode,
        "query": query_str,
        "total": len(results),
    }


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="KB Index query")
    parser.add_argument("query", help="Query string")
    parser.add_argument("--dir", required=True, help="Knowledge base root directory")
    parser.add_argument(
        "--mode",
        default="keyword",
        choices=["keyword", "semantic", "hybrid"],
        help="Query mode"
    )
    args = parser.parse_args()

    try:
        result = query(args.query, Path(args.dir), args.mode)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
