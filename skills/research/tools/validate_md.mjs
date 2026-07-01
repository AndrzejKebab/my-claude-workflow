#!/usr/bin/env node
// Validate LaTeX (KaTeX) and Mermaid blocks supplied as JSON on stdin.
// Input format: [{kind, content, start_line, end_line, file}, ...]
//   kind ∈ {"inline", "display", "mermaid"}
// Output (stdout): same array with {ok: bool|null, error?: string} merged into each entry.
//   ok = true   parsed cleanly
//   ok = false  parser raised an error (block has a syntax problem)
//   ok = null   validator unavailable (e.g. mermaid load failed)

import { readFileSync } from "node:fs";
import katex from "katex";

const raw = readFileSync(0, "utf8");
let blocks;
try {
  blocks = JSON.parse(raw);
} catch (e) {
  process.stderr.write(`validate_md: invalid JSON on stdin: ${e.message}\n`);
  process.exit(2);
}

let mermaidCache = null;
async function loadMermaid() {
  if (mermaidCache !== null) return mermaidCache;
  try {
    const { JSDOM } = await import("jsdom");
    const dom = new JSDOM("<!DOCTYPE html><html><body></body></html>", {
      pretendToBeVisual: true,
    });
    // Assign DOM globals defensively: modern Node (21+) exposes some of these
    // (notably `navigator`) as read-only built-in getters, and a plain
    // `globalThis.navigator = …` throws "Cannot set property … which has only a
    // getter", which previously aborted mermaid setup entirely and silently
    // downgraded every diagram to an unvalidated warning. Swallow the read-only
    // failures — mermaid.parse only needs window/document/DOM, not navigator.
    const assignGlobal = (key, value) => {
      try {
        globalThis[key] = value;
      } catch {
        try {
          Object.defineProperty(globalThis, key, { value, configurable: true, writable: true });
        } catch {
          /* read-only, non-configurable built-in — leave Node's version in place */
        }
      }
    };
    assignGlobal("window", dom.window);
    assignGlobal("document", dom.window.document);
    assignGlobal("navigator", dom.window.navigator);
    assignGlobal("HTMLElement", dom.window.HTMLElement);
    assignGlobal("Element", dom.window.Element);
    assignGlobal("Node", dom.window.Node);
    assignGlobal("SVGElement", dom.window.SVGElement);
    assignGlobal("DOMParser", dom.window.DOMParser);
    assignGlobal("XMLSerializer", dom.window.XMLSerializer);
    const mod = await import("mermaid");
    const mermaid = mod.default ?? mod;
    if (typeof mermaid.parse !== "function") {
      throw new Error("mermaid.parse is not a function (incompatible mermaid version?)");
    }
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "loose",
      logLevel: 5,
    });
    mermaidCache = { ok: true, mermaid };
  } catch (e) {
    mermaidCache = { ok: false, error: `mermaid validator unavailable: ${e.message}` };
  }
  return mermaidCache;
}

function validateLatex(content, displayMode) {
  try {
    katex.renderToString(content, {
      throwOnError: true,
      strict: "warn",
      displayMode,
      trust: true,
      macros: {},
    });
    return { ok: true };
  } catch (e) {
    let msg = e?.message ?? String(e);
    msg = msg.replace(/\[[0-9;]*m/g, "");
    return { ok: false, error: msg };
  }
}

async function validateMermaid(content) {
  const m = await loadMermaid();
  if (!m.ok) {
    return { ok: null, error: m.error };
  }
  try {
    await m.mermaid.parse(content, { suppressErrors: false });
    return { ok: true };
  } catch (e) {
    let msg = e?.message ?? String(e);
    msg = msg.replace(/\[[0-9;]*m/g, "");
    return { ok: false, error: msg };
  }
}

const results = [];
for (const blk of blocks) {
  let r;
  if (blk.kind === "inline") {
    r = validateLatex(blk.content, false);
  } else if (blk.kind === "display") {
    r = validateLatex(blk.content, true);
  } else if (blk.kind === "mermaid") {
    r = await validateMermaid(blk.content);
  } else {
    r = { ok: null, error: `unknown kind: ${blk.kind}` };
  }
  results.push({ ...blk, ...r });
}

process.stdout.write(JSON.stringify(results));
