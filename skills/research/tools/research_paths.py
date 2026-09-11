"""Shared, cross-platform storage paths for the research workflow."""

from __future__ import annotations

import os
from pathlib import Path


DEFAULT_RESEARCH_ROOT = Path(r"F:\Programowanie\my-claude-workflow\research-library")
RESEARCH_ROOT = Path(os.environ.get("RESEARCH_ROOT", DEFAULT_RESEARCH_ROOT)).expanduser()
PREPARED_DIR = RESEARCH_ROOT / "Prepared"
ARTICLES_DIR = RESEARCH_ROOT / "Articles"
ASSETS_DIR = PREPARED_DIR / "assets"
