#!/usr/bin/env python3
"""
轻量知识图谱系统 - 主入口
将文件索引升级为支持关系查询的知识图谱
"""

import argparse
import json
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict

class KBGraph:
    def __init__(self, kb_dir: str):
        self.kb_dir = Path(kb_dir)
        self.workdir = self.kb_dir / ".kb-workdir"

        # 加载本体
        self.ontology = self._load_json("kb-ontology.json")

        # 加载数据
        self.entries = self._load_json("entries.json")
        self.entities_registry = self._load_json("entities-registry.json") if (self.workdir / "entities-registry.json").exists() else {}
        self.graph_data = self._load_json("graph-data.json") if (self.workdir / "graph-data.json").exists() else {}

    def _load_json(self, filename: str) -> Any:
        path = self.workdir / filename
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_json(self, data: Any, filename: str):
        path = self.workdir / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_entity_type_id(self, entity_name: str) -> str:
        """根据实体名称推断类型"""
        entity_lower = entity_name.lower()

        # 关键词匹配规则
        type_keywords = {
            "technology": ["cli", "api", "protocol", "mcp", "github", "git", "markdown", "jwt", "openapi", "rust", "typescript", "python", "代码", "协议", "接口"],
            "product": ["claude code", "openclaw", "cursor", "aider", "copilot", "agent", "bot", "平台", "系统", "工具"],
            "organization": ["anthropic", "openai", "google", "mit", "公司", "机构"],
            "concept": ["rag", "llm", "ai agent", "设计模式", "协作", "记忆", "规划", "反思", "路由"],
            "agent_framework": ["langchain", "crewai", "agentspace", "hermes", "框架"],
            "document": ["codex", "card", "规范", "文档", "书"]
        }

        for type_id, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in entity_lower:
                    return type_id

        # 默认返回 concept
        return "concept"

    def extract_key_entities(self, entry: Dict[str, Any]) -> List[Dict[str, str]]:
        """从文档条目中提取关键实体（最多2个）"""
        raw_entities = entry.get("entities", [])
        title = entry.get("title", "")
        summary = entry.get("summary", "")

        # 如果已有实体且带类型，直接使用
        if raw_entities and len(raw_entities) <= 2:
            # 检查是否已有类型标注
            if isinstance(raw_entities[0], dict):
                return raw_entities

        # 选择最重要的1-2个实体
        # 优先级：标题中出现的 > summary中前提到的
        key_entities = []

        # 先找标题中的实体
        for entity in raw_entities:
            if entity.lower() in title.lower() and len(key_entities) < 2:
                entity_type = self.get_entity_type_id(entity)
                key_entities.append({
                    "name": entity,
                    "type": entity_type
                })

        # 如果还没够2个，从summary补充
        if len(key_entities) < 2:
            for entity in raw_entities:
                entity_name = entity if isinstance(entity, str) else entity.get("name", "")
                if entity_name.lower() in summary.lower() and not any(e["name"] == entity_name for e in key_entities):
                    entity_type = self.get_entity_type_id(entity_name)
                    key_entities.append({
                        "name": entity_name,
                        "type": entity_type
                    })
                    if len(key_entities) >= 2:
                        break

        # 如果还是不够，直接取前2个
        if len(key_entities) < 2 and raw_entities:
            for entity in raw_entities:
                entity_name = entity if isinstance(entity, str) else entity.get("name", "")
                if not any(e["name"] == entity_name for e in key_entities):
                    entity_type = self.get_entity_type_id(entity_name)
                    key_entities.append({
                        "name": entity_name,
                        "type": entity_type
                    })
                    if len(key_entities) >= 2:
                        break

        return key_entities

    def build_entities_registry(self) -> Dict[str, Any]:
        """构建实体注册表"""
        registry = {}

        for path, entry in self.entries.items():
            key_entities = self.extract_key_entities(entry)

            for entity_obj in key_entities:
                entity_name = entity_obj["name"]
                entity_type = entity_obj["type"]

                if entity_name not in registry:
                    registry[entity_name] = {
                        "name": entity_name,
                        "type": entity_type,
                        "documents": [],
                        "related_entities": []
                    }

                if path not in registry[entity_name]["documents"]:
                    registry[entity_name]["documents"].append(path)

        return registry

    def build_graph_relations(self) -> Dict[str, List[Dict]]:
        """构建图谱关系"""
        relations = defaultdict(list)

        # 为每个文档提取的实体建立关系
        for path, entry in self.entries.items():
            key_entities = self.extract_key_entities(entry)

            if len(key_entities) >= 2:
                # 在同一文档中出现的实体建立 related_to 关系
                for i, e1 in enumerate(key_entities):
                    for e2 in key_entities[i+1:]:
                        relation = {
                            "subject": e1["name"],
                            "object": e2["name"],
                            "relation": "related_to",
                            "source": path,
                            "evidence": f"在文档 '{entry.get('title', path)}' 中同时出现"
                        }
                        relations[e1["name"]].append(relation)

                        # 反向关系
                        reverse_relation = {
                            "subject": e2["name"],
                            "object": e1["name"],
                            "relation": "related_to",
                            "source": path,
                            "evidence": f"在文档 '{entry.get('title', path)}' 中同时出现"
                        }
                        relations[e2["name"]].append(reverse_relation)

        return dict(relations)

    def build(self):
        """构建知识图谱"""
        print("📊 构建知识图谱...")

        # 1. 构建实体注册表
        print("  → 构建实体注册表...")
        self.entities_registry = self.build_entities_registry()
        self._save_json(self.entities_registry, "entities-registry.json")
        print(f"    ✓ 注册了 {len(self.entities_registry)} 个实体")

        # 2. 构建关系图谱
        print("  → 构建关系图谱...")
        self.graph_data = self.build_graph_relations()
        self._save_json(self.graph_data, "graph-data.json")
        total_relations = sum(len(rels) for rels in self.graph_data.values())
        print(f"    ✓ 构建了 {total_relations} 条关系")

        # 3. 更新 entries.json，为每个条目添加带类型的实体
        print("  → 更新文档条目...")
        updated_entries = {}
        for path, entry in self.entries.items():
            updated_entry = entry.copy()
            key_entities = self.extract_key_entities(entry)
            updated_entry["entities"] = key_entities
            updated_entries[path] = updated_entry

        self.entries = updated_entries
        self._save_json(self.entries, "entries.json")
        print(f"    ✓ 更新了 {len(self.entries)} 个文档条目")

        print("\n✅ 知识图谱构建完成!")
        self.print_stats()

    def print_stats(self):
        """打印统计信息"""
        print("\n📈 知识图谱统计:")
        print(f"  文档总数: {len(self.entries)}")
        print(f"  实体总数: {len(self.entities_registry)}")

        # 实体类型分布
        type_counts = defaultdict(int)
        for entity in self.entities_registry.values():
            type_counts[entity["type"]] += 1

        print(f"  实体类型分布:")
        for type_id, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            type_name = next((t["name"] for t in self.ontology["entity_types"] if t["id"] == type_id), type_id)
            print(f"    {type_name}: {count}")

        # 关系统计
        total_relations = sum(len(rels) for rels in self.graph_data.values())
        print(f"  关系总数: {total_relations}")

        # 验证约束
        violations = [k for k, v in self.entries.items() if len(v.get("entities", [])) > 2]
        if violations:
            print(f"  ⚠️  违反约束的文档: {len(violations)} 篇")
        else:
            print(f"  ✓ 所有文档符合≤2实体约束")

    def preprocess_query(self, query_text: str) -> List[str]:
        """预处理查询文本，提取有意义的关键词"""
        # 停用词：语法词 + 高频无区分度词
        stop_words = {
            # 语法词
            "和", "与", "或", "的", "了", "是", "在", "有", "中", "对", "等", "及", "以及",
            # 高频无区分度词（在技术文档中出现率 >30%，无法缩小搜索范围）
            "自动", "生成", "实现", "方案", "方法", "如何", "什么", "一个", "这个", "可以",
            "使用", "进行", "通过", "基于", "支持", "提供", "包括", "以及", "还有",
            "对比", "比较", "分析", "研究", "介绍", "分享", "开源", "工具",
        }

        # 1. 先提取完整短语（用空格和标点分割）
        words = []
        current_word = ""
        for char in query_text:
            if char in " \t\n\r，。、；：？！""''（）【】《》":
                if current_word:
                    words.append(current_word)
                    current_word = ""
            else:
                current_word += char
        if current_word:
            words.append(current_word)

        # 2. 过滤停用词，保留有意义的完整短语
        meaningful_words = [w for w in words if w not in stop_words and len(w) > 1]

        if not meaningful_words:
            return [query_text]

        # 3. 展开驼峰命名的英文词（如 ClaudeCode → Claude, Code）
        expanded = []
        for word in meaningful_words:
            expanded.append(word)
            if any(c.isupper() for c in word[1:]):  # 驼峰
                parts = []
                current_part = ""
                for c in word:
                    if c.isupper() and current_part and not current_part[-1].isupper():
                        parts.append(current_part)
                        current_part = c
                    else:
                        current_part += c
                if current_part:
                    parts.append(current_part)
                for part in parts:
                    if len(part) >= 2 and part != word:
                        expanded.append(part)

        # 4. 对纯中文短语（没有空格分隔的），尝试用已知实体名切分
        # 先从实体注册表构建实体名列表（按长度降序，优先匹配长实体）
        entity_names = sorted(
            [name for name in self.entities_registry.keys()],
            key=len, reverse=True
        )
        entity_names_lower = {name.lower(): name for name in entity_names}

        seen = set()
        final = []
        for word in expanded:
            # 先直接加入
            if word not in seen:
                seen.add(word)
                final.append(word)

            # 对包含中文的词，尝试从中找出已知实体
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in word)
            if has_chinese and len(word) > 3:
                word_lower = word.lower()
                for ent_lower, ent_name in entity_names_lower.items():
                    if ent_lower in word_lower and len(ent_name) >= 3:
                        if ent_name not in seen:
                            seen.add(ent_name)
                            final.append(ent_name)

        return final

    def query(self, query_text: str, mode: str = "keyword") -> Dict[str, Any]:
        """查询知识图谱"""
        results = []

        if mode == "keyword":
            # 预处理查询，提取关键词
            keywords = self.preprocess_query(query_text)

            # 对每个关键词进行搜索
            for query_keyword in keywords:
                query_lower = query_keyword.lower()

                # 1. 搜索实体
                for entity_name, entity_data in self.entities_registry.items():
                    if query_lower in entity_name.lower():
                        for doc_path in entity_data["documents"]:
                            if doc_path in self.entries:
                                entry = self.entries[doc_path]
                                # 检查是否已存在
                                if not any(r["document"]["path"] == doc_path for r in results):
                                    result = {
                                        "type": "entity_match",
                                        "matched_entity": entity_name,
                                        "matched_keyword": query_keyword,
                                        "entity_type": entity_data["type"],
                                        "document": {
                                            "path": doc_path,
                                            "title": entry.get("title", ""),
                                            "summary": entry.get("summary", ""),
                                            "entities": entry.get("entities", [])
                                        },
                                        "relevance": "high" if query_lower == entity_name.lower() else "medium"
                                    }
                                    results.append(result)

                # 2. 搜索文档标题和摘要
                for path, entry in self.entries.items():
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")

                    if query_lower in title.lower() or query_lower in summary.lower():
                        # 避免重复
                        if not any(r["document"]["path"] == path for r in results):
                            result = {
                                "type": "document_match",
                                "matched_keyword": query_keyword,
                                "document": {
                                    "path": path,
                                    "title": title,
                                    "summary": summary,
                                    "entities": entry.get("entities", [])
                                },
                                "relevance": "high" if query_lower in title.lower() else "medium"
                            }
                            results.append(result)

        # 按相关性排序
        results.sort(key=lambda x: (
            x["relevance"] == "high",
        ), reverse=True)

        return {
            "query": query_text,
            "keywords": keywords if mode == "keyword" else [],
            "mode": mode,
            "results": results[:20]  # 限制返回前20个结果
        }

def main():
    parser = argparse.ArgumentParser(description="轻量知识图谱系统")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # build 命令
    build_parser = subparsers.add_parser("build", help="构建知识图谱")
    build_parser.add_argument("--dir", required=True, help="知识库目录")

    # query 命令
    query_parser = subparsers.add_parser("query", help="查询知识图谱")
    query_parser.add_argument("query_text", help="查询文本")
    query_parser.add_argument("--dir", required=True, help="知识库目录")
    query_parser.add_argument("--mode", default="keyword", choices=["keyword", "graph"], help="查询模式")

    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="显示统计信息")
    stats_parser.add_argument("--dir", required=True, help="知识库目录")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    kb = KBGraph(args.dir)

    if args.command == "build":
        kb.build()
    elif args.command == "query":
        result = kb.query(args.query_text, args.mode)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.command == "stats":
        kb.print_stats()

if __name__ == "__main__":
    main()
