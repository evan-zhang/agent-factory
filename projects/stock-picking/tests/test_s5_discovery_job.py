#!/usr/bin/env python3
"""Tests for discovery cron wrapper behavior."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "src" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import discovery_job


def test_wrote_draft_detects_current_run_draft():
    assert discovery_job.wrote_draft({"written": [{"schema": "draft_candidates.v1"}]}) is True
    assert discovery_job.wrote_draft({"written": [{"schema": "run_context.v1"}]}) is False
    assert discovery_job.wrote_draft({"calendar_skip": True, "written": []}) is False
