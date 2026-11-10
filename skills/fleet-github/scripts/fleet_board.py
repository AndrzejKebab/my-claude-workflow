#!/usr/bin/env python3
"""Order the project's open issues and PRs from their declared dependencies. Programs started: gh.

Reads GitHub once, parses what each item depends on, and prints the queue in the
order it can actually be worked — plus the faults that make a queue lie:

  * a `Blocked by #N` naming a closed issue (the block is stale)
  * an item labelled `blocked` with no `Blocked by` line (nobody can act on it)
  * a PR with no issue link (`Refs`/`Closes`), or an issue claimed `in-progress`
    with no PR open against it (invisible work)
  * a cycle

Usage:
    python fleet_board.py                 # queue + faults for open items
    python fleet_board.py --faults-only   # just the faults
    python fleet_board.py --json          # machine-readable
    python fleet_board.py --markdown      # a table for a docs page
    python fleet_board.py --repo owner/name  (default: gh's current repo)

Exit codes: 0 clean, 1 faults found, 2 gh failed.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

BLOCK_RE = re.compile(r"blocked\s+by\s*:?\s*((?:#\d+[\s,]*)+)", re.IGNORECASE)
LINK_RE = re.compile(r"\b(?:closes|close|fixes|fix|refs|references?)\s+#(\d+)", re.IGNORECASE)
STATUS = {
    "ready", "in-progress", "waits-for-review", "in-review",
    "waits-for-final-review", "ready-to-merge", "blocked",
    "needs-owner", "needs-human", "on-hold",
}


def gh(*args: str) -> str:
    out = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        print(out.stderr.strip() or "gh failed", file=sys.stderr)
        sys.exit(2)
    return out.stdout


def fetch(repo: str | None) -> tuple[list[dict], list[dict]]:
    who = ["-R", repo] if repo else []
    issues = json.loads(gh("issue", "list", "--state", "open", "--limit", "200",
                           "--json", "number,title,labels,body,assignees", *who))
    prs = json.loads(gh("pr", "list", "--state", "open", "--limit", "200",
                        "--json", "number,title,labels,body,headRefName,isDraft", *who))
    return issues, prs


def labels(item: dict) -> list[str]:
    return [l["name"] for l in item.get("labels", [])]


def blockers(body: str) -> list[int]:
    found: list[int] = []
    for group in BLOCK_RE.findall(body or ""):
        found += [int(n) for n in re.findall(r"#(\d+)", group)]
    return found


def build(issues, prs):
    items = {}
    for it in issues:
        items[it["number"]] = {"kind": "issue", "number": it["number"], "title": it["title"],
                               "labels": labels(it), "blockers": blockers(it.get("body", "")),
                               "links": [int(n) for n in LINK_RE.findall(it.get("body", ""))]}
    for pr in prs:
        items[pr["number"]] = {"kind": "pr", "number": pr["number"], "title": pr["title"],
                               "labels": labels(pr), "blockers": blockers(pr.get("body", "")),
                               "links": [int(n) for n in LINK_RE.findall(pr.get("body", ""))],
                               "head": pr.get("headRefName"), "draft": pr.get("isDraft")}
    return items


def faults(items) -> list[str]:
    out: list[str] = []
    pr_links = {n for it in items.values() if it["kind"] == "pr" for n in it["links"]}
    for it in items.values():
        tag = f"#{it['number']}"
        st = [l for l in it["labels"] if l in STATUS]
        if len(st) > 1:
            out.append(f"{tag} has {len(st)} status labels: {', '.join(st)}")
        if "blocked" in it["labels"] and not it["blockers"]:
            out.append(f"{tag} is labelled blocked but names no 'Blocked by' issue")
        if it["blockers"]:
            closed = [b for b in it["blockers"] if b not in items]
            if closed and "blocked" not in it["labels"]:
                out.append(f"{tag} depends on closed/missing {closed} but is not labelled blocked")
        if it["kind"] == "pr" and not it["links"]:
            out.append(f"{tag} (PR) names no issue: add Refs/Closes")
        if it["kind"] == "pr" and it["draft"] and "in-progress" not in it["labels"]:
            out.append(f"{tag} is a draft PR without in-progress")
        if it["kind"] == "issue" and "in-progress" in it["labels"] and it["number"] not in pr_links:
            out.append(f"{tag} is in-progress with no open PR linking it")
    # cycles
    for start in items:
        seen, stack = set(), [start]
        while stack:
            cur = stack.pop()
            if cur in seen:
                out.append(f"dependency cycle through #{start}")
                break
            seen.add(cur)
            stack += [b for b in items[cur]["blockers"] if b in items]
    return sorted(set(out))


def order(items) -> list[list[dict]]:
    remaining = dict(items)
    waves, done = [], set()
    while remaining:
        wave = [it for it in remaining.values()
                if all(b in done or b not in items for b in it["blockers"])]
        if not wave:  # cycle: dump the rest so nothing is silently dropped
            wave = list(remaining.values())
        waves.append(sorted(wave, key=lambda i: i["number"]))
        for it in wave:
            done.add(it["number"])
            remaining.pop(it["number"], None)
    return waves


def render(waves, found, as_json=False, markdown=False) -> str:
    if as_json:
        return json.dumps({"waves": waves, "faults": found}, indent=2, ensure_ascii=False)
    lines: list[str] = []
    if markdown:
        lines += ["| Wave | Item | Kind | Labels | Blocked by |", "|---|---|---|---|---|"]
        for i, wave in enumerate(waves, 1):
            for it in wave:
                lines.append(f"| {i} | #{it['number']} {it['title'][:60]} | {it['kind']} | "
                             f"{', '.join(it['labels']) or '-'} | "
                             f"{', '.join(f'#{b}' for b in it['blockers']) or '-'} |")
    else:
        for i, wave in enumerate(waves, 1):
            lines.append(f"wave {i}:")
            for it in wave:
                lab = f" [{', '.join(it['labels'])}]" if it["labels"] else ""
                blk = f"  <- {', '.join(f'#{b}' for b in it['blockers'])}" if it["blockers"] else ""
                lines.append(f"  #{it['number']:<4} {it['kind']:<5}{lab}{blk}")
                lines.append(f"        {it['title'][:90]}")
    lines.append("")
    if found:
        lines.append("faults:")
        lines += [f"  - {f}" for f in found]
    else:
        lines.append("faults: none")
    return "\n".join(lines)


def is_active(item: dict) -> bool:
    """Something the fleet is actually working on: a status label or a Worker owner."""
    lab = item["labels"]
    return any(l in STATUS for l in lab) or any(l.startswith("worker:") for l in lab)


def body_blockers(item: dict, repo: str | None, kind: str) -> list[int]:
    """Blockers from the body; for a `blocked` item with none, fall back to its recent comments.

    The dependency is often stated in the comment that set the label rather than in the body, and a
    queue that ignores that reports every such item as an undiagnosed block. Only the last few
    comments are read, and only for items that need it.
    """
    found = blockers(item.get("body", ""))
    if found or "blocked" not in item["labels"]:
        return found
    who = ["-R", repo] if repo else []
    sub = ["pr"] if kind == "pr" else ["issue"]
    try:
        raw = gh(*sub, "view", str(item["number"]), "--json", "comments", *who)
    except SystemExit:
        return []
    comments = json.loads(raw).get("comments", [])[-3:]
    for c in comments:
        found = blockers(c.get("body", ""))
        if found:
            return found
    return []


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", help="owner/name; default is gh's current repo")
    ap.add_argument("--faults-only", action="store_true")
    ap.add_argument("--all", action="store_true", help="include issues with no status/worker label")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--markdown", action="store_true")
    a = ap.parse_args()

    issues, prs = fetch(a.repo)
    items = build(issues, prs)
    if not a.all:
        items = {n: it for n, it in items.items() if is_active(it)}
    for it in items.values():
        if not it["blockers"] and "blocked" in it["labels"]:
            it["blockers"] = body_blockers({"number": it["number"], "labels": it["labels"],
                                            "body": ""}, a.repo, it["kind"])
    found = faults(items)
    waves = order(items)

    if a.faults_only:
        print("\n".join(found) if found else "faults: none")
    else:
        print(render(waves, found, a.json, a.markdown))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
