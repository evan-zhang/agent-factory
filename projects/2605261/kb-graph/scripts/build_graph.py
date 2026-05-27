#!/usr/bin/env python3
"""KB Graph 图谱层：从 entries.json 构建节点/边 + Louvain 社区发现"""
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

def build_graph_from_entries(root):
    """从 entries 构建节点和边"""
    entries = load_entries(root)

    # 节点
    nodes = []
    for rel_path, entry in entries.items():
        nodes.append({
            "id": rel_path,
            "title": entry.get("title", rel_path),
            "tags": entry.get("tags", []),
            "entities": entry.get("entities", []),
            "sha256": entry.get("sha256", ""),
        })

    # 边：共享 entity → 边
    entity_map = {}  # entity -> list of file paths
    for rel_path, entry in entries.items():
        for ent in entry.get("entities", []):
            if ent not in entity_map:
                entity_map[ent] = []
            entity_map[ent].append(rel_path)

    edges = []
    for entity, paths in entity_map.items():
        if len(paths) < 2:
            continue
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                edges.append({
                    "from": paths[i],
                    "to": paths[j],
                    "type": "entity",
                    "label": entity,
                    "weight": 1.0
                })

    # 边：共享 tag → 边（权重低于 entity）
    tag_map = {}  # tag -> list of file paths
    for rel_path, entry in entries.items():
        for tag in entry.get("tags", []):
            if tag not in tag_map:
                tag_map[tag] = []
            tag_map[tag].append(rel_path)

    for tag, paths in tag_map.items():
        if len(paths) < 2:
            continue
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                edges.append({
                    "from": paths[i],
                    "to": paths[j],
                    "type": "tag",
                    "label": tag,
                    "weight": 0.3
                })

    # 边：relationships → 边（引用关系和主题关联）
    for rel_path, entry in entries.items():
        for rel in entry.get("relationships", []):
            rel_type = rel.get("type", "unknown")
            target = rel.get("target", "")
            description = rel.get("description", "")

            if not target:
                continue

            # 尝试在 entries 中查找目标文件
            target_files = []
            for other_path in entries.keys():
                if target.lower() in other_path.lower():
                    target_files.append(other_path)

            # 根据关系类型设置权重
            if rel_type == "reference":
                weight = 0.8
            elif rel_type == "topic":
                weight = 0.5
            else:
                weight = 0.3

            # 创建边
            for target_file in target_files:
                if target_file == rel_path:
                    continue
                edges.append({
                    "from": rel_path,
                    "to": target_file,
                    "type": rel_type,
                    "label": target,
                    "description": description,
                    "weight": weight
                })

    return nodes, edges

def run_louvain_community(nodes, edges):
    """Louvain 社区检测"""
    try:
        import networkx as nx
        import community as community_louvain
    except ImportError:
        return simple_community_detection(nodes, edges)

    G = nx.Graph()
    for node in nodes:
        G.add_node(node["id"])
    for edge in edges:
        G.add_edge(edge["from"], edge["to"], weight=edge.get("weight", 1.0))

    if G.number_of_nodes() == 0:
        return []

    partition = community_louvain.best_partition(G)
    comm_map = {}
    for node_id, comm_id in partition.items():
        comm_map.setdefault(comm_id, []).append(node_id)

    communities = []
    for comm_id, members in comm_map.items():
        communities.append({"name": f"社区{comm_id+1}", "members": members, "size": len(members)})
    return communities

def simple_community_detection(nodes, edges):
    if not nodes:
        return []
    return [{"name": "社区1", "members": [n["id"] for n in nodes], "size": len(nodes)}]

def main():
    import argparse
    parser = argparse.ArgumentParser(description="KB Graph 图谱构建")
    parser.add_argument("--dir", required=True, help="知识库根目录")
    parser.add_argument("--output", help="输出图谱 JSON 路径（可选）")
    args = parser.parse_args()

    root = Path(args.dir)
    nodes, edges = build_graph_from_entries(root)
    communities = run_louvain_community(nodes, edges)

    result = {
        "ok": True,
        "nodes": nodes,
        "edges": edges,
        "communities": communities,
        "stats": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "community_count": len(communities),
        }
    }

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False))
        print(json.dumps({"ok": True, "output": args.output, **result["stats"]}))
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
