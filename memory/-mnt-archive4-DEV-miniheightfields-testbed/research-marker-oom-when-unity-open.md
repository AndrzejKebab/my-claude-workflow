---
name: research-marker-oom-when-unity-open
description: /research marker extraction CUDA-OOMs mid-batch when the Unity editor is open; gate each paper on free VRAM and retry — never force CPU
metadata: 
  node_type: memory
  type: reference
  originSessionId: b2bcd4ec-09b1-43a7-90fe-fbd6c15fb6e3
  modified: 2026-07-21T17:51:07.670Z
---

`/research` Pass 1 is **GPU-only by deliberate policy** (`marker_extract.py:364`, "user,
2026-05-30"): marker on GPU + Anthropic Sonnet is the only accepted extraction path for this
corpus. `_require_marker_gpu()` rejects an explicitly-empty `CUDA_VISIBLE_DEVICES`, and
`extract_research.py` refuses the PyMuPDF span-walker fallback. Both refusals are the point —
the previous silent CPU downgrade read downstream as "marker worked but produced poor output".
**Never work around this by forcing CPU.** A VRAM shortfall is meant to be a loud operator-visible
failure.

The gate samples free VRAM **once**, before torch imports, and needs only 3072 MiB — but the policy
comment expects ~15 GiB free. On this workstation a live Unity editor plus the usual Electron GPU
processes (Orca IDE ×2, Vivaldi, Cider, 1Password) hold ~6 GiB steady and spike higher, so a batch
**passes the gate and then OOMs mid-run on a later paper**. Observed 2026-07-21: paper 1 succeeded,
paper 2 died with `Tried to allocate 162.00 MiB ... 388.62 MiB is free`.

**How to apply:** keep GPU inference; make the *runner* resilient instead. Before each paper, poll
until free VRAM clears a bar well above the 3 GiB gate (~6 GiB), and retry a paper that OOMs rather
than continuing past it. Make the runner skip slugs whose `<slug>.md` already exists —
`extract_research.py` without `--force` writes a `.regen` sidecar instead of erroring, which reads
as success. Per-paper `assets/<slug>/marker.md` caching makes a resumed batch cheap.

Two traps that cost time here:

- `pkill -f extract-batch` from the Bash tool matches the tool's *own* command line and kills the
  calling shell (exit 144) — and any Monitor watching the log. Bracket it: `pkill -f 'extract[-]batch'`.
- A failed extraction still archives its source PDF if the runner `cp`s unconditionally. A PDF in
  `/mnt/archive4/PAPERS/` is **not** evidence the extraction succeeded — check `marker: yes` and a
  non-zero md line count per paper.
- **The inverse bites harder: a present `<slug>.md` is not evidence the PDF was archived.** A resume
  guard of the form `[ -s "$PREP/$slug.md" ] && skip` short-circuits *every* later step for that
  paper, including the archive copy. Kill a batch between a paper's extraction and its `cp` and the
  resumed run skips it forever, silently. Observed 2026-07-21 — one of nine papers reached a
  finished, refined markdown entry whose `source:` still pointed into the staging dir, with no PDF
  in the archive at all. **Verify the archive as a separate closing sweep** (`for s in $slugs; do
  [ -f "$ARC/$s.pdf" ] || echo MISS $s; done`), never as a side effect of the extraction loop. Also
  repoint `source:` at `/mnt/archive4/PAPERS/<slug>.pdf` rather than the staging path — the corpus
  has older entries pointing at long-gone `~/Downloads` files, and that is what the archive exists
  to prevent.

Related: [[research-background-jobs-need-setsid]].
