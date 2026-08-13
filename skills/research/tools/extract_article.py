#!/usr/bin/env python3
"""Fetch a web article (blog post, devlog, release-notes page) and convert it
to OKF-schema markdown for the /mnt/archive4/PAPERS/Articles corpus.

This covers the /research input class the PDF/PPTX/video scripts don't:
a plain HTML article. Invoked per-URL:

    extract_article.py <url> --slug=SLUG [--title TITLE] [--author AUTHOR] [--force]

Output matches the corpus's existing <slug>.html + <slug>.md pairing
convention (see e.g. Articles/bittker-making-sandspiel.{html,md}): the raw
fetched HTML is archived as <slug>.html, images/videos referenced in the
article body are downloaded to assets/<slug>/, and the body is converted to
markdown (fenced code blocks with language, tables, headings, lists) under a
hand-written OKF frontmatter block. `description` and `tags` are left as
TODO placeholders -- for a small extraction the /research skill's own
guidance is to skip the three-agent dance and fill these by hand rather than
dispatching a refiner.
"""

import argparse
import copy
import datetime
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Comment
from markdownify import markdownify as md_convert

ARTICLES_DIR = Path("/mnt/archive4/PAPERS/Articles")
ASSETS_DIR = ARTICLES_DIR / "assets"

UA = "Mozilla/5.0 (X11; Linux x86_64) research-skill/1.0"

# Ordered content-region heuristics. Every match across every selector is
# scored by rendered text length and the longest wins -- sites like bevy.org
# repeat the same class on a near-empty hero wrapper *and* the real body, so
# picking the first match is wrong.
CONTENT_SELECTORS = [
    ("div", {"class": "news-content"}),  # bevy.org
    ("article", {}),
    ("div", {"itemprop": "articleBody"}),
    ("div", {"class": re.compile(r"\bpost-content\b")}),
    ("div", {"class": re.compile(r"\bentry-content\b")}),
    ("div", {"class": re.compile(r"\barticle-body\b")}),
    ("main", {}),
]

STRIP_TAGS = ["script", "style", "nav", "footer", "svg", "noscript", "iframe"]


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def find_content(soup: BeautifulSoup):
    """Try selectors in priority order; within the first selector that yields
    a plausible match, keep the longest (a site may repeat the same class on
    a near-empty wrapper *and* the real body -- bevy.org does this for its
    hero-image div vs. the actual article div). Do NOT fall through to a more
    generic selector once a specific one has matched: `main`/`article` wrap
    the whole page (title, subtitle, sidebar nav) and will usually be
    *longer* than the real content region, which is exactly wrong."""
    for name, attrs in CONTENT_SELECTORS:
        candidates = [el for el in soup.find_all(name, attrs=attrs) if len(el.get_text(strip=True)) > 200]
        if candidates:
            return max(candidates, key=lambda el: len(el.get_text(strip=True)))
    return None


def code_language(el) -> str:
    """markdownify code_language_callback: prefer <code data-lang="...">
    (Zola/syntect output) over class="language-*" (the more common convention)."""
    code = el.find("code")
    if not code:
        return ""
    if code.get("data-lang"):
        return code["data-lang"]
    for c in code.get("class") or []:
        if c.startswith("language-"):
            return c[len("language-") :]
        if c.startswith("lang-"):
            return c[len("lang-") :]
    return ""


def download_asset(url: str, dest_dir: Path) -> str | None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = Path(urlparse(url).path).name or "asset"
    dest = dest_dir / name
    if not dest.exists():
        try:
            dest.write_bytes(fetch(url))
        except Exception as exc:  # noqa: BLE001 -- one bad asset shouldn't kill the run
            print(f"  ! failed to download {url}: {exc}", file=sys.stderr)
            return None
    return name


def clean_and_localize(content, page_url: str, slug: str) -> None:
    """Mutates `content` in place: strips noise tags/heading anchors,
    downloads image/video assets to assets/<slug>/ and rewrites their src to
    the relative path, and resolves link hrefs to absolute URLs."""
    for tag in content.find_all(STRIP_TAGS):
        tag.decompose()
    for c in content.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for a in content.find_all("a", class_="anchor-link"):
        a.decompose()

    # <details>/<summary> (collapsible sections) aren't in markdownify's
    # block-tag registry, so its content gets glued onto whatever text
    # precedes it with no line break. Turn the summary into its own <p> and
    # unwrap <details> so its children fall into normal block-level flow.
    for details in content.find_all("details"):
        summary = details.find("summary")
        if summary:
            p = BeautifulSoup(f"<p>{summary.decode_contents()}</p>", "lxml").p
            summary.replace_with(p)
        details.unwrap()

    asset_dir = ASSETS_DIR / slug
    for img in content.find_all("img"):
        src = img.get("src")
        if not src:
            continue
        name = download_asset(urljoin(page_url, src), asset_dir)
        if name:
            img["src"] = f"assets/{slug}/{name}"

    for video in content.find_all("video"):
        source = video.find("source")
        src = source.get("src") if source else video.get("src")
        if not src:
            video.decompose()
            continue
        name = download_asset(urljoin(page_url, src), asset_dir)
        link_md = f"[Video: {name}](assets/{slug}/{name})" if name else f"[Video]({urljoin(page_url, src)})"
        video.replace_with(BeautifulSoup(f"<p>{link_md}</p>", "lxml").p)

    for a in content.find_all("a", href=True):
        a["href"] = urljoin(page_url, a["href"])


def html_to_markdown(content) -> str:
    text = md_convert(
        str(content),
        heading_style="ATX",
        bullets="-",
        code_language_callback=code_language,
    )
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url")
    ap.add_argument("--slug", required=True)
    ap.add_argument("--title")
    ap.add_argument("--author")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    out_md = ARTICLES_DIR / f"{args.slug}.md"
    if out_md.exists() and not args.force:
        print(f"refusing to overwrite {out_md} (pass --force)", file=sys.stderr)
        sys.exit(1)

    print(f"fetching {args.url}")
    raw = fetch(args.url)
    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)
    (ARTICLES_DIR / f"{args.slug}.html").write_bytes(raw)

    soup = BeautifulSoup(raw, "lxml")
    content = find_content(soup)
    if content is None:
        print("could not locate an article content region", file=sys.stderr)
        sys.exit(1)
    content = copy.deepcopy(content)

    title = args.title
    if not title:
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else (soup.title.get_text(strip=True) if soup.title else args.slug)

    clean_and_localize(content, args.url, args.slug)
    body_md = html_to_markdown(content)

    lines = [
        "---",
        "type: Technical Article",
        f'title: "{title}"',
        "description: TODO",
        "medium: html",
        f"source_url: {args.url}",
    ]
    if args.author:
        lines.append(f"author: {args.author}")
    lines += [
        f"extracted: {datetime.date.today().isoformat()}",
        f"slug: {args.slug}",
        "tags:",
        "  - TODO",
        "---",
        "",
        f"# {title}",
        "",
        body_md,
        "",
    ]
    out_md.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_md} ({len(body_md)} chars body)")


if __name__ == "__main__":
    main()
