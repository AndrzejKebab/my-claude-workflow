#!/usr/bin/env python3
"""Maintain the OKF topic-index pages for the PAPERS corpus.

Topic membership is derived from each document's frontmatter `tags` — the single
source of truth — and the per-tag pages under `<bundle>/topics/` are regenerated
to match. The generation is idempotent: re-running after any tag change converges
to the correct state (adds a page when a tag reaches two members, refreshes member
tables, rewrites the topic index). A page's human/LLM-written intro paragraph is
preserved across regenerations; only the member table (between the
`<!-- members:start -->` / `<!-- members:end -->` markers) is owned by this script.

Usage:
    update_topics.py --only=<slug>     # rebuild the bundle that contains <slug>
    update_topics.py --bundle=Prepared # rebuild one bundle
    update_topics.py --all             # rebuild every bundle (default)
    update_topics.py --check           # report what would change, write nothing
    update_topics.py --prune           # also delete topic pages whose tag fell below two members
"""
from __future__ import annotations

import argparse
import contextlib
import fcntl
import os
import re
import sys

CORPUS = "/mnt/archive4/PAPERS"
BUNDLES = ["Prepared", "Articles"]
MIN_MEMBERS = 2  # a tag needs at least this many documents to get its own page

ACRONYMS = {
    "gpu", "cpu", "gpgpu", "simd", "gi", "aa", "taa", "ssr", "ssao", "sdf", "svo",
    "svdag", "hzb", "vsm", "csm", "esm", "lod", "pbr", "fft", "api", "ca", "fp",
    "ibl", "brdf", "hdr", "bvh", "ui", "io", "mip", "vof", "ffd", "mrpnn", "restir",
    "dmd", "oit", "msaa", "amd", "rdr2", "ue", "2d", "3d", "obdd", "ssa", "fpga", "llm",
}

START = "<!-- members:start -->"
END = "<!-- members:end -->"


# --------------------------------------------------------------------- parsing

def split_frontmatter(text: str):
    """Return (frontmatter_block, body). frontmatter_block is '' if absent."""
    t = text.lstrip("\n")
    m = re.match(r"^---\n(.*?)\n---\n?", t, re.DOTALL)
    if not m:
        return "", text
    return m.group(1), t[m.end():]


def parse_frontmatter(block: str) -> dict:
    """Minimal YAML-subset parser: scalar `key: value` lines plus a `tags`
    field in either inline (`[a, b]`) or block (`- a` / `- b`) form."""
    data: dict = {}
    lines = block.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^([A-Za-z0-9_]+):\s?(.*)$", line)
        if not m:
            i += 1
            continue
        key, val = m.group(1), m.group(2).strip()
        if key == "tags":
            if val.startswith("["):
                inner = val.strip("[]").strip()
                data["tags"] = [t.strip().strip("'\"") for t in inner.split(",") if t.strip()]
            else:
                tags = []
                j = i + 1
                while j < len(lines) and re.match(r"^\s*-\s+", lines[j]):
                    tags.append(re.sub(r"^\s*-\s+", "", lines[j]).strip().strip("'\""))
                    j += 1
                data["tags"] = tags
                i = j
                continue
        else:
            data[key] = val.strip("'\"")
        i += 1
    return data


def title_case(tag: str) -> str:
    return " ".join(w.upper() if w in ACRONYMS else w.capitalize() for w in tag.split("-"))


def esc(cell: str) -> str:
    return (cell or "").replace("|", r"\|").replace("\n", " ").strip()


# ------------------------------------------------------------------ membership

def collect_documents(bundle_dir: str) -> list[dict]:
    docs = []
    for name in sorted(os.listdir(bundle_dir)):
        if not name.endswith(".md") or name.startswith("index"):
            continue
        path = os.path.join(bundle_dir, name)
        if not os.path.isfile(path):
            continue
        block, _ = split_frontmatter(open(path, encoding="utf-8", errors="replace").read())
        if not block:
            continue
        fm = parse_frontmatter(block)
        docs.append({
            "slug": fm.get("slug") or name[:-3],
            "title": fm.get("title") or name[:-3],
            "type": fm.get("type") or "",
            "description": fm.get("description") or "",
            "tags": fm.get("tags") or [],
        })
    return docs


def membership(docs: list[dict]) -> dict:
    tags: dict = {}
    for d in docs:
        for t in d["tags"]:
            tags.setdefault(t, []).append(d)
    for t in tags:
        tags[t].sort(key=lambda d: (d["type"], d["title"].lower()))
    return tags


# ------------------------------------------------------------------ rendering

def extract_intro(existing: str) -> str | None:
    """The intro is the body text between the `# H1` and the member table
    (or its start marker). Returns None when there is no existing page."""
    if existing is None:
        return None
    _, body = split_frontmatter(existing)
    body = body.lstrip("\n")
    body = re.sub(r"^#\s+.*\n", "", body, count=1).lstrip("\n")  # drop the H1
    for stop in (START, "\n| "):
        idx = body.find(stop)
        if idx != -1:
            body = body[:idx]
    body = body.split("\n|", 1)[0]  # belt-and-braces for a leading table
    return body.strip() or None


def render_topic_page(bundle: str, tag: str, members: list[dict], existing: str | None) -> str:
    fm_existing = parse_frontmatter(split_frontmatter(existing)[0]) if existing else {}
    title = fm_existing.get("title") or title_case(tag)
    desc = fm_existing.get("description") or f"Documents in the {bundle} bundle tagged `{tag}`."
    intro = extract_intro(existing) or f"Documents in the {bundle} bundle tagged `{tag}`."

    rows = ["| Document | Kind | Summary |", "|---|---|---|"]
    for d in members:
        rows.append(f"| [{esc(d['title'])}](../{d['slug']}.md) | {esc(d['type'])} | {esc(d['description'])} |")
    table = "\n".join(rows)

    return (
        "---\n"
        "type: Topic Index\n"
        f"title: {title}\n"
        f"description: {desc}\n"
        f"tags: [{tag}]\n"
        "---\n\n"
        f"# {title}\n\n"
        f"{intro}\n\n"
        f"{START}\n{table}\n{END}\n"
    )


def render_index(bundle: str, tag_counts: list[tuple[str, int]]) -> str:
    tag_counts = sorted(tag_counts, key=lambda tc: (-tc[1], tc[0]))
    rows = ["| Topic | Documents |", "|---|---|"]
    for tag, count in tag_counts:
        rows.append(f"| [{tag}](./{tag}.md) | {count} |")
    return (
        "---\n"
        "type: Topic Index\n"
        f"title: {bundle} — Topic Index\n"
        "slug: topics-index\n"
        "---\n\n"
        f"# {bundle} — Topic Index\n\n"
        "Each topic page links every document in the "
        f"{bundle} bundle tagged with that topic. Generated by `update_topics.py`.\n\n"
        + "\n".join(rows) + "\n"
    )


# --------------------------------------------------------------------- driver

@contextlib.contextmanager
def bundle_lock(bundle_dir: str):
    """Exclusive per-bundle advisory lock. Two refiners finishing different
    papers in parallel both rebuild the same bundle and write the same shared
    files (`topics/index.md`, any co-tagged page); serializing the whole
    read-derive-write makes the last writer observe every paper already on disk,
    so no update is lost and no file is written half-formed. Blocking on purpose
    — a rebuild is sub-second, so a waiter just runs immediately after."""
    os.makedirs(bundle_dir, exist_ok=True)
    lock_path = os.path.join(bundle_dir, ".topics-update.lock")
    fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def write_if_changed(path: str, content: str, check: bool, changes: list):
    old = open(path, encoding="utf-8").read() if os.path.exists(path) else None
    if old == content:
        return
    changes.append(("update" if old is not None else "create", path))
    if not check:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        # Atomic publish: a concurrent reader sees either the old or new file
        # whole, never a partial write. os.replace is atomic within a filesystem.
        tmp = f"{path}.tmp.{os.getpid()}"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)


def rebuild_bundle(bundle: str, check: bool, prune: bool) -> list:
    bundle_dir = os.path.join(CORPUS, bundle)
    with bundle_lock(bundle_dir):
        return _rebuild_bundle_locked(bundle, bundle_dir, check, prune)


def _rebuild_bundle_locked(bundle: str, bundle_dir: str, check: bool, prune: bool) -> list:
    topics_dir = os.path.join(bundle_dir, "topics")
    docs = collect_documents(bundle_dir)
    tags = membership(docs)
    keep = {t: mem for t, mem in tags.items() if len(mem) >= MIN_MEMBERS}

    changes: list = []
    for tag, mem in keep.items():
        path = os.path.join(topics_dir, f"{tag}.md")
        existing = open(path, encoding="utf-8").read() if os.path.exists(path) else None
        write_if_changed(path, render_topic_page(bundle, tag, mem, existing), check, changes)

    # orphan pages: a topic file whose tag no longer reaches MIN_MEMBERS
    if os.path.isdir(topics_dir):
        for name in sorted(os.listdir(topics_dir)):
            if not name.endswith(".md") or name == "index.md":
                continue
            tag = name[:-3]
            if tag not in keep:
                path = os.path.join(topics_dir, name)
                if prune:
                    changes.append(("delete", path))
                    if not check:
                        os.remove(path)
                else:
                    changes.append(("orphan", path))

    index_path = os.path.join(topics_dir, "index.md")
    write_if_changed(index_path, render_index(bundle, [(t, len(m)) for t, m in keep.items()]), check, changes)
    return changes


def bundle_of_slug(slug: str) -> str | None:
    for bundle in BUNDLES:
        if os.path.isfile(os.path.join(CORPUS, bundle, f"{slug}.md")):
            return bundle
    return None


def main():
    ap = argparse.ArgumentParser(description="Maintain OKF topic-index pages from frontmatter tags.")
    ap.add_argument("--only", help="rebuild the bundle containing this slug")
    ap.add_argument("--bundle", choices=BUNDLES, help="rebuild a single bundle")
    ap.add_argument("--all", action="store_true", help="rebuild every bundle (default)")
    ap.add_argument("--check", action="store_true", help="report changes without writing")
    ap.add_argument("--prune", action="store_true", help="delete pages whose tag fell below the member threshold")
    args = ap.parse_args()

    if args.only:
        bundle = bundle_of_slug(args.only)
        if not bundle:
            print(f"error: no document found for slug '{args.only}' in {BUNDLES}", file=sys.stderr)
            return 2
        targets = [bundle]
    elif args.bundle:
        targets = [args.bundle]
    else:
        targets = BUNDLES

    total = 0
    for bundle in targets:
        changes = rebuild_bundle(bundle, args.check, args.prune)
        total += len([c for c in changes if c[0] != "orphan"])
        for action, path in changes:
            print(f"  {action:7} {os.path.relpath(path, CORPUS)}")
        print(f"{bundle}: {len(changes)} change(s)")
    if args.check and total:
        print(f"\n{total} file(s) would change (run without --check to apply)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
