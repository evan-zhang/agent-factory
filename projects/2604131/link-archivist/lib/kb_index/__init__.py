"""
KB Index - Link Archivist internal knowledge indexing module.

This module provides incremental indexing, query, and maintenance capabilities
for archived Markdown reports. It's designed to be lightweight and dependency-free.

Core modules:
- parse_frontmatter: Extract entry from YAML frontmatter (no LLM)
- update_single: Incremental single-file update with fcntl lock
- ingest: Directory scanning and change detection
- compile: LLM-based compilation (for force-rebuild only)
- build_graph: Build entity relationship graph from entries
- query_engine: Keyword/semantic/hybrid query modes
- lint: Index health checks
"""

__version__ = "2.0.0"

from .parse_frontmatter import parse_entry
from .update_single import update_single, ConcurrentUpdateError
from .query_engine import query
from .lint import lint_index

__all__ = [
    "parse_entry",
    "update_single",
    "ConcurrentUpdateError",
    "query",
    "lint_index",
]
