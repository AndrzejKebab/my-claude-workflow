---
name: browser-downloads-land-in-papers
description: "Chrome on this machine saves downloads to /mnt/archive4/PAPERS, not ~/Downloads, and blocks page→localhost requests"
metadata: 
  node_type: memory
  type: reference
  originSessionId: 1d0936ad-11fa-4cea-88e5-c578ec1ed021
  modified: 2026-08-13T16:01:03.815Z
---

Claude-in-Chrome downloads land in `/mnt/archive4/PAPERS` (Chrome's configured download
directory), under a generated UUID name when the page sets `download` without a user gesture.
Look there, newest first — not `~/Downloads`, which is where the user's own saved files go.

Chrome also refuses a page on the public internet any request to this machine (private-network
blocking): a `fetch` from an https page to `http://127.0.0.1:PORT` hangs and never reaches a
local server, so a "POST the data to a localhost sink" pipeline cannot work. Move the data with
a Blob download instead (`type: "application/octet-stream"` so it saves rather than navigates).

**Why:** two hours were lost building a local HTTP sink for the Confluence import before the
block was diagnosed, and then looking for the bundle in the wrong directory.

**How to apply:** for browser→disk transfers, save a single JSON bundle and read it from
`/mnt/archive4/PAPERS`. The repo's own instance of this is `tools/confluence-import/`.
