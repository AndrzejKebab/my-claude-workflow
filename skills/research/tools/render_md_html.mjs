#!/usr/bin/env node
// Compile a research markdown file to a self-contained HTML preview.
// LaTeX is rendered server-side via KaTeX (so syntax errors paint red in the page);
// Mermaid is left as <pre class="mermaid"> and rendered client-side via a CDN script
// (mermaid's server-side renderer requires headless Chromium and is too heavy to ship).
//
// Usage: node render_md_html.mjs <input.md> <output.html>

import { readFileSync, writeFileSync } from "node:fs";
import { basename } from "node:path";
import MarkdownIt from "markdown-it";
import katexPlugin from "@vscode/markdown-it-katex";

const [, , inPath, outPath] = process.argv;
if (!inPath || !outPath) {
  process.stderr.write("Usage: render_md_html.mjs <input.md> <output.html>\n");
  process.exit(2);
}

const md = new MarkdownIt({ html: true, linkify: true, typographer: false });
md.use(katexPlugin.default ?? katexPlugin, {
  throwOnError: false,
  errorColor: "#cc0000",
  strict: "warn",
});

const originalFence = md.renderer.rules.fence;
md.renderer.rules.fence = function (tokens, idx, options, env, self) {
  const tok = tokens[idx];
  const lang = (tok.info || "").trim().toLowerCase();
  if (lang === "mermaid") {
    return `<pre class="mermaid">\n${tok.content}</pre>\n`;
  }
  return originalFence(tokens, idx, options, env, self);
};

const source = readFileSync(inPath, "utf8");
const body = md.render(source);

const title = basename(inPath);
const html = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>${title}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<style>
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
       max-width: 920px; margin: 2em auto; padding: 0 1em; line-height: 1.55; color: #222; }
h1, h2, h3, h4 { line-height: 1.25; }
img { max-width: 100%; height: auto; }
pre { background: #f6f8fa; padding: 0.75em; overflow-x: auto; border-radius: 4px; }
code { background: #f6f8fa; padding: 0 0.2em; border-radius: 3px; font-size: 0.92em; }
pre code { background: none; padding: 0; font-size: inherit; }
blockquote { border-left: 3px solid #ddd; color: #555; margin: 1em 0; padding: 0.2em 1em; }
.katex-error { color: #cc0000 !important; border-bottom: 2px wavy #cc0000; }
table { border-collapse: collapse; }
table th, table td { border: 1px solid #ddd; padding: 0.3em 0.6em; }
.mermaid { background: #fff; padding: 1em; border: 1px solid #eee; border-radius: 4px; }
</style>
</head>
<body>
${body}
<script type="module">
import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
mermaid.initialize({ startOnLoad: true, securityLevel: "loose" });
</script>
</body>
</html>
`;

writeFileSync(outPath, html);
process.stderr.write(`render_md_html: wrote ${outPath}\n`);
