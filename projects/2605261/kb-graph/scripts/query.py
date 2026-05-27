#!/usr/bin/env python3
"""KB Graph 查询层：基于 entries.json 的关键词 + 向量查询"""
import json
import re
from pathlib import Path

def load_entries(root):
    """从 .kb-workdir/entries.json 加载所有条目"""
    entries_path = Path(root) / ".kb-workdir" / "entries.json"
    if not entries_path.exists():
        return {}
    with open(entries_path) as f:
        return json.load(f)

def load_embeddings(root):
    """从 .kb-workdir/embeddings.json 加载向量索引"""
    embeddings_path = Path(root) / ".kb-workdir" / "embeddings.json"
    if not embeddings_path.exists():
        return {}
    with open(embeddings_path) as f:
        return json.load(f)

def save_embeddings(root, embeddings):
    """保存向量索引到 .kb-workdir/embeddings.json"""
    embeddings_path = Path(root) / ".kb-workdir" / "embeddings.json"
    embeddings_path.parent.mkdir(parents=True, exist_ok=True)
    with open(embeddings_path, "w") as f:
        json.dump(embeddings, f, indent=2, ensure_ascii=False)

def get_text_embedding(text):
    """使用 OpenAI embeddings API 生成向量"""
    import os
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in environment")

    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        response = client.embeddings.create(
            input=text[:8191],  # OpenAI 限制
            model="text-embedding-3-small"
        )
        return response.data[0].embedding
    except Exception as e:
        raise RuntimeError(f"Failed to generate embedding: {e}")

def cosine_similarity(vec1, vec2):
    """计算余弦相似度"""
    import numpy as np
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0
    return dot_product / (norm1 * norm2)

def search_by_keyword(root, query_str):
    """关键词搜索：title / summary / tags / entities"""
    entries = load_entries(root)
    results = []
    q = query_str.lower()
    for rel_path, entry in entries.items():
        title = entry.get("title", "").lower()
        summary = entry.get("summary", "").lower()
        tags = " ".join([t.lower() for t in entry.get("tags", [])])
        entities = " ".join([e.lower() for e in entry.get("entities", [])])
        score = 0
        if q in title:
            score += 10
        if q in summary:
            score += 5
        if q in tags:
            score += 3
        if q in entities:
            score += 3
        if score > 0:
            results.append({"score": score, "entry": entry, "rel_path": rel_path})
    results.sort(key=lambda x: -x["score"])
    return results[:10]

def search_by_semantic(root, query_str):
    """语义搜索：使用向量相似度"""
    entries = load_entries(root)
    embeddings = load_embeddings(root)

    # 生成查询向量
    try:
        query_embedding = get_text_embedding(query_str)
    except RuntimeError as e:
        # 如果无法生成向量，返回空结果
        return []

    results = []
    for rel_path, embedding in embeddings.items():
        if rel_path in entries:
            similarity = cosine_similarity(query_embedding, embedding)
            results.append({
                "score": similarity,
                "entry": entries[rel_path],
                "rel_path": rel_path
            })

    results.sort(key=lambda x: -x["score"])
    return results[:10]

def search_by_hybrid(root, query_str):
    """混合搜索：融合关键词和语义结果"""
    keyword_results = search_by_keyword(root, query_str)
    semantic_results = search_by_semantic(root, query_str)

    # 合并结果，避免重复
    combined = {}
    for r in keyword_results:
        path = r["rel_path"]
        combined[path] = {
            "score": r["score"],
            "entry": r["entry"],
            "rel_path": path,
            "keyword_score": r["score"],
            "semantic_score": 0
        }

    for r in semantic_results:
        path = r["rel_path"]
        if path in combined:
            combined[path]["semantic_score"] = r["score"]
            # 加权融合：关键词 60%，语义 40%
            combined[path]["score"] = combined[path]["keyword_score"] * 0.6 + r["score"] * 0.4
        else:
            combined[path] = {
                "score": r["score"] * 0.4,  # 只有语义分数时降权
                "entry": r["entry"],
                "rel_path": path,
                "keyword_score": 0,
                "semantic_score": r["score"]
            }

    # 排序并返回前 10 个结果
    results = sorted(combined.values(), key=lambda x: -x["score"])[:10]
    return results

def query(query_str, root, mode="keyword"):
    """主查询入口

    Args:
        query_str: 查询字符串
        root: 知识库根目录
        mode: 查询模式 (keyword/semantic/hybrid)
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
                "semantic_score": round(r.get("semantic_score", 0), 4)
            }
            for r in results
        ],
        "method": mode,
        "query": query_str,
        "total": len(results),
    }

def main():
    import argparse
    parser = argparse.ArgumentParser(description="KB Graph 查询")
    parser.add_argument("--query", required=True)
    parser.add_argument("--dir", required=True, help="知识库根目录")
    parser.add_argument("--mode", default="keyword", choices=["keyword", "semantic", "hybrid"],
                        help="查询模式")
    args = parser.parse_args()

    result = query(args.query, args.dir, args.mode)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
