#!/usr/bin/env python3
"""
Unit and integration tests for KB Export OKF module.

Tests:
- Export to temp KB → verify index.md, log.md, archive/ created
- Re-run without --force → idempotent
- Re-run with --force → clean rebuild
- Empty entries → graceful index.md
- Missing entries.json → error JSON
"""
import json
import sys
import tempfile
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))

# Import test helper
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from kb_export_okf import export_okf


def create_test_md(md_path: Path, content: str) -> None:
    """Create test Markdown file with content."""
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(content, encoding="utf-8")


def create_workdir_entries(workdir: Path, entries: dict) -> None:
    """Create entries.json in workdir."""
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "entries.json").write_text(
        json.dumps(entries, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def create_workdir_cache(workdir: Path, cache: dict) -> None:
    """Create kb_cache.json in workdir."""
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "kb_cache.json").write_text(
        json.dumps(cache, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def create_workdir_stats(workdir: Path, stats: dict) -> None:
    """Create build_stats.json in workdir."""
    workdir.mkdir(parents=True, exist_ok=True)
    (workdir / "build_stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


def test_export_full():
    """Test full export to temp KB."""
    print("Testing full export...")

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        # Create test markdown files
        md1 = archive_dir / "2026" / "06" / "K-260619-001.md"
        md2 = archive_dir / "2026" / "06" / "K-260619-002.md"

        create_test_md(md1, """---
archive: K-260619-001
source: https://example.com/1
source_type: url
created_at: 2026-06-19T10:00:00
summary: First test document
entities:
  - EntityA
  - EntityB
tags:
  - AI
  - Test
confidence: high
---

# First Document

Content of first document.
""")

        create_test_md(md2, """---
archive: K-260619-002
source: https://example.com/2
source_type: url
created_at: 2026-06-19T11:00:00
summary: Second test document
entities:
  - EntityB
  - EntityC
tags:
  - Architecture
  - Test
confidence: medium
---

# Second Document

Content of second document.
""")

        # Create workdir with entries, cache, stats
        workdir = archive_dir / ".kb-workdir"
        create_workdir_entries(workdir, {
            "2026/06/K-260619-001.md": {
                "title": "First Document",
                "summary": "First test document",
                "entities": ["EntityA", "EntityB"],
                "tags": ["AI", "Test"],
                "archive_id": "K-260619-001",
                "source": "https://example.com/1",
                "source_type": "url",
                "created_at": "2026-06-19T10:00:00",
                "confidence": "high",
            },
            "2026/06/K-260619-002.md": {
                "title": "Second Document",
                "summary": "Second test document",
                "entities": ["EntityB", "EntityC"],
                "tags": ["Architecture", "Test"],
                "archive_id": "K-260619-002",
                "source": "https://example.com/2",
                "source_type": "url",
                "created_at": "2026-06-19T11:00:00",
                "confidence": "medium",
            },
        })

        create_workdir_cache(workdir, {
            "2026/06/K-260619-001.md": {
                "status": "ok",
                "indexed_at": "2026-06-19T10:05:00",
            },
            "2026/06/K-260619-002.md": {
                "status": "ok",
                "indexed_at": "2026-06-19T11:05:00",
            },
        })

        create_workdir_stats(workdir, {
            "last_build": "2026-06-19T12:00:00",
            "total_entries": 2,
            "last_entry_path": "2026/06/K-260619-002.md",
        })

        # Run export
        result = export_okf(archive_dir)

        # Verify result
        assert result["ok"] is True, f"Export failed: {result}"
        assert result["concepts_exported"] == 2
        assert result["index_generated"] is True
        assert result["log_generated"] is True

        export_dir = archive_dir / ".kb-workdir" / "okf-export"

        # Verify index.md exists and contains key elements
        index_path = export_dir / "index.md"
        assert index_path.exists(), "index.md not created"
        index_content = index_path.read_text(encoding="utf-8")
        assert "Knowledge Bundle Index" in index_content
        assert "Total concepts: 2" in index_content
        assert "First Document" in index_content
        assert "Second Document" in index_content
        assert "**AI** (1 concepts)" in index_content
        assert "**Architecture** (1 concepts)" in index_content
        assert "**Test** (2 concepts)" in index_content

        # Verify log.md exists
        log_path = export_dir / "log.md"
        assert log_path.exists(), "log.md not created"
        log_content = log_path.read_text(encoding="utf-8")
        assert "Knowledge Bundle Change Log" in log_content
        assert "Total entries: 2" in log_content

        # Verify archive files copied
        archive_dir_export = export_dir / "archive"
        assert (archive_dir_export / "2026" / "06" / "K-260619-001.md").exists()
        assert (archive_dir_export / "2026" / "06" / "K-260619-002.md").exists()

        # Verify copied files have same content
        original_md1_content = md1.read_text(encoding="utf-8")
        copied_md1_content = (archive_dir_export / "2026" / "06" / "K-260619-001.md").read_text(encoding="utf-8")
        assert original_md1_content == copied_md1_content

    print("✅ Full export test passed")


def test_export_idempotent():
    """Test re-running export without --force is idempotent."""
    print("Testing idempotent export...")

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        # Create single test file
        md1 = archive_dir / "2026" / "06" / "K-260619-001.md"
        create_test_md(md1, """---
archive: K-260619-001
source: https://example.com/1
source_type: url
created_at: 2026-06-19T10:00:00
summary: Test document
entities:
  - EntityA
tags:
  - AI
confidence: high
---

# Test Document

Content.
""")

        # Create minimal workdir
        workdir = archive_dir / ".kb-workdir"
        create_workdir_entries(workdir, {
            "2026/06/K-260619-001.md": {
                "title": "Test Document",
                "summary": "Test document",
                "entities": ["EntityA"],
                "tags": ["AI"],
                "archive_id": "K-260619-001",
                "source": "https://example.com/1",
                "source_type": "url",
                "created_at": "2026-06-19T10:00:00",
                "confidence": "high",
            },
        })
        create_workdir_cache(workdir, {})
        create_workdir_stats(workdir, {})

        export_dir = archive_dir / ".kb-workdir" / "okf-export"

        # First export
        result1 = export_okf(archive_dir)
        assert result1["ok"] is True

        # Record timestamp
        index_path = export_dir / "index.md"
        first_index_content = index_path.read_text(encoding="utf-8")
        first_timestamp = result1.get("timestamp")

        # Second export without --force
        result2 = export_okf(archive_dir)
        assert result2["ok"] is True
        assert result2["concepts_exported"] == 1

        # Verify index was regenerated (timestamp should differ)
        second_index_content = index_path.read_text(encoding="utf-8")
        assert first_timestamp != result2.get("timestamp")

    print("✅ Idempotent export test passed")


def test_export_force_rebuild():
    """Test --force rebuilds cleanly."""
    print("Testing force rebuild...")

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        # Create test file
        md1 = archive_dir / "2026" / "06" / "K-260619-001.md"
        create_test_md(md1, """---
archive: K-260619-001
source: https://example.com/1
source_type: url
created_at: 2026-06-19T10:00:00
summary: Test document
entities:
  - EntityA
tags:
  - AI
confidence: high
---

# Test Document

Content.
""")

        # Create minimal workdir
        workdir = archive_dir / ".kb-workdir"
        create_workdir_entries(workdir, {
            "2026/06/K-260619-001.md": {
                "title": "Test Document",
                "summary": "Test document",
                "entities": ["EntityA"],
                "tags": ["AI"],
                "archive_id": "K-260619-001",
                "source": "https://example.com/1",
                "source_type": "url",
                "created_at": "2026-06-19T10:00:00",
                "confidence": "high",
            },
        })
        create_workdir_cache(workdir, {})
        create_workdir_stats(workdir, {})

        export_dir = archive_dir / ".kb-workdir" / "okf-export"

        # First export
        result1 = export_okf(archive_dir)
        assert result1["ok"] is True

        # Create a marker file in export to verify it gets deleted
        marker = export_dir / "marker.txt"
        marker.write_text("This should be deleted on --force")

        # Verify marker exists
        assert marker.exists()

        # Force rebuild
        result2 = export_okf(archive_dir, force=True)
        assert result2["ok"] is True

        # Verify marker was deleted
        assert not marker.exists(), "Force rebuild should delete existing export"

        # Verify export is still valid
        assert (export_dir / "index.md").exists()
        assert (export_dir / "log.md").exists()
        assert (export_dir / "archive" / "2026" / "06" / "K-260619-001.md").exists()

    print("✅ Force rebuild test passed")


def test_export_empty_entries():
    """Test graceful handling of empty entries."""
    print("Testing empty entries...")

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        # Create workdir with empty entries
        workdir = archive_dir / ".kb-workdir"
        create_workdir_entries(workdir, {})

        export_dir = archive_dir / ".kb-workdir" / "okf-export"

        # Export
        result = export_okf(archive_dir)
        assert result["ok"] is True
        assert result["concepts_exported"] == 0
        assert result.get("note") == "No concepts to export"

        # Verify index exists with graceful message
        index_path = export_dir / "index.md"
        assert index_path.exists()
        index_content = index_path.read_text(encoding="utf-8")
        assert "Total concepts: 0" in index_content
        assert "No concepts indexed yet" in index_content

    print("✅ Empty entries test passed")


def test_export_missing_entries():
    """Test error handling for missing entries.json."""
    print("Testing missing entries.json...")

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        # Create workdir but no entries.json
        workdir = archive_dir / ".kb-workdir"
        workdir.mkdir(parents=True, exist_ok=True)

        # Export should fail
        result = export_okf(archive_dir)
        assert result["ok"] is False
        assert "error" in result
        assert "entries.json not found" in result["error"]
        assert "hint" in result

    print("✅ Missing entries.json test passed")


def test_export_invalid_output_dir():
    """Test error handling for invalid output directory."""
    print("Testing invalid output directory...")

    with tempfile.TemporaryDirectory() as tmpdir:
        archive_dir = Path(tmpdir)

        # Create minimal workdir
        workdir = archive_dir / ".kb-workdir"
        create_workdir_entries(workdir, {
            "2026/06/K-260619-001.md": {
                "title": "Test",
                "summary": "Test",
                "entities": [],
                "tags": [],
                "archive_id": "K-260619-001",
                "source": "",
                "source_type": "",
                "created_at": "2026-06-19T10:00:00",
                "confidence": "medium",
            },
        })

        # Try to export outside .kb-workdir
        invalid_out = archive_dir / "invalid-export"
        result = export_okf(archive_dir, output_dir=invalid_out)

        assert result["ok"] is False
        assert "must be inside .kb-workdir" in result["error"]

    print("✅ Invalid output directory test passed")


def main():
    """Run all tests."""
    print("Running KB Export OKF tests...\n")

    tests = [
        test_export_full,
        test_export_idempotent,
        test_export_force_rebuild,
        test_export_empty_entries,
        test_export_missing_entries,
        test_export_invalid_output_dir,
    ]

    failed = []

    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"❌ {test.__name__} failed: {e}")
            failed.append(test.__name__)
        except Exception as e:
            print(f"❌ {test.__name__} error: {e}")
            failed.append(test.__name__)

    print("\n" + "=" * 50)
    if failed:
        print(f"❌ {len(failed)} test(s) failed:")
        for name in failed:
            print(f"  - {name}")
        return 1
    else:
        print(f"✅ All {len(tests)} tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
