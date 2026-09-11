#!/usr/bin/env python3
"""Copy a verified Markdown note into shared or project-owned memory."""

from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path


def category_path(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise argparse.ArgumentTypeError("category must be a relative path without '..'")
    return path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tier", choices=("shared", "project"))
    parser.add_argument("source", type=Path)
    parser.add_argument("--workflow-root", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--category", type=category_path, default=Path())
    parser.add_argument("--name", help="destination filename; defaults to source name")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    if not source.is_file():
        parser.error(f"source is not a file: {source}")
    if source.suffix.lower() != ".md":
        parser.error("source must be a Markdown file")

    name = args.name or source.name
    if Path(name).name != name or not name.lower().endswith(".md"):
        parser.error("name must be a Markdown filename without directories")

    if args.tier == "shared":
        if args.workflow_root is None:
            parser.error("shared memory requires --workflow-root")
        root = args.workflow_root.expanduser().resolve()
        destination_dir = root / "memory" / "shared" / args.category
    else:
        if args.project_root is None:
            parser.error("project memory requires --project-root")
        root = args.project_root.expanduser().resolve()
        if not (root / ".git").exists() and not (root / "ProjectSettings").exists():
            parser.error(f"project root is not recognizable: {root}")
        destination_dir = root / "docs" / "agent-memory" / args.category

    destination = destination_dir / name
    if destination.exists():
        if destination.is_file() and digest(source) == digest(destination):
            print(f"Already current: {destination}")
            return 0
        parser.error(f"destination exists with different content: {destination}")

    if args.dry_run:
        print(f"Would copy: {source} -> {destination}")
        return 0

    destination_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if digest(source) != digest(destination):
        destination.unlink(missing_ok=True)
        raise RuntimeError("copy verification failed; destination removed")
    print(f"Stored: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
