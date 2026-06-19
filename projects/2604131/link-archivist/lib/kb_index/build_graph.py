#!/usr/bin/env python3
"""
Build graph from entries: nodes, edges, and Louvain community detection.

This module constructs relationship graphs from indexed entries.
It's used for full rebuilds and graph visualization.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple


def load_entries(root: Path) -> Dict[str, Any]:
    """Load entries from .kb-workdir/entries.json."""
    entries_path = Path(root) / ".kb-workdir" / "entries.json"
    if not entries_path.exists():
        return {}
    try:
        return json.loads(entries_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def build_graph_from_entries(root: Path) -> Tuple[List[Dict], List[Dict]]:
    """Build nodes and edges from entries.

    Args:
        root: Knowledge base root directory

    Returns:
        (nodes, edges) tuple
    """
    entries = load_entries(root)
    if not entries:
        return [], []

    # Build nodes
    nodes = []
    for rel_path, entry in entries.items():
        nodes.append({
            "id": rel_path,
            "title": entry.get("title", rel_path),
            "tags": entry.get("tags", []),
            "entities": entry.get("entities", []),
            "sha256": entry.get("source_sha256", ""),
        })

    # Build edges from shared entities
    entity_map = {}
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

    # Build edges from shared tags
    tag_map = {}
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

    # Build edges from relationships
    for rel_path, entry in entries.items():
        relationships = entry.get("relationships", [])
        if not isinstance(relationships, list):
            continue
        for rel in relationships:
            if not isinstance(rel, dict):
                continue
            rel_type = rel.get("type", "unknown")
            target = rel.get("target", "")
            description = rel.get("description", "")

            if not target:
                continue

            # Find target in entries
            target_files = []
            for other_path in entries.keys():
                if target.lower() in other_path.lower():
                    target_files.append(other_path)

            # Set weight by relationship type
            if rel_type == "reference":
                weight = 0.8
            elif rel_type == "topic":
                weight = 0.5
            else:
                weight = 0.3

            # Create edges
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


def run_louvain_community(nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
    """Run Louvain community detection.

    Args:
        nodes: List of node dicts
        edges: List of edge dicts

    Returns:
        List of community dicts
    """
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
        communities.append({
            "name": f"社区{comm_id+1}",
            "members": members,
            "size": len(members)
        })
    return communities


def simple_community_detection(nodes: List[Dict], edges: List[Dict]) -> List[Dict]:
    """Simple fallback community detection (all in one).

    Args:
        nodes: List of node dicts
        edges: List of edge dicts

    Returns:
        Single community with all nodes
    """
    if not nodes:
        return []
    return [{
        "name": "社区1",
        "members": [n["id"] for n in nodes],
        "size": len(nodes)
    }]


def build_graph(root: Path, output_path: Path = None) -> Dict[str, Any]:
    """Build complete graph structure.

    Args:
        root: Knowledge base root directory
        output_path: Optional output file path

    Returns:
        Graph data with nodes, edges, communities, stats
    """
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

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))

    return result


def main():
    """CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(description="KB Index graph builder")
    parser.add_argument("--dir", required=True, help="Knowledge base root directory")
    parser.add_argument("--output", help="Output JSON file path")
    args = parser.parse_args()

    try:
        result = build_graph(Path(args.dir), Path(args.output) if args.output else None)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
