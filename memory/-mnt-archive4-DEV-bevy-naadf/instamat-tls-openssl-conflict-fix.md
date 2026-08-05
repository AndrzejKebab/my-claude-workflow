---
name: instamat-tls-openssl-conflict-fix
description: InstaMAT Studio on CachyOS — deep-link + TLS fixed (desktop typo + bundled OpenSSL-1.1 libcurl)
metadata: 
  node_type: memory
  type: project
  originSessionId: b3fde672-9476-4aa5-8b37-9cbf894a3080
---

`/opt/InstaMATStudio` (InstaMAT Studio 3.0, bundled Qt 6.5.3) had two bugs on this CachyOS box, both fixed 2026-05-14:

1. **Deep link `instamatstudiopolyverseintegration://` ignored** — vendor's `/usr/share/applications/instamat-studio.desktop` has a typo in `MimeType` (`instamatsudio...`, missing `t`). Fixed with a user-level override at `~/.local/share/applications/instamat-studio.desktop` (correct MimeType + `xdg-mime default`).

2. **"TLS initialization failed, error 99"** — bundled Qt's `plugins/tls/libqopensslbackend.so` hard-links **OpenSSL 1.1**, but system `libcurl.so.4` (DT_NEEDED by the binary) links **OpenSSL 3** → both load in one process → Qt TLS init fails. Fixed by building **curl 8.8.0 against `openssl-1.1`** (curl ≥8.20 dropped 1.1 support) and dropping it at `/opt/InstaMATStudio/lib/libcurl.so.4` — the binary's RUNPATH `$ORIGIN/lib` makes it shadow the system libcurl. InstaMAT only uses 5 trivial curl_easy symbols.

**Why:** vendor builds assume system libcurl uses OpenSSL 1.1 (true on old Ubuntu/RHEL, false on Arch/CachyOS).
**How to apply:** an InstaMAT update may overwrite `/opt/.../lib/libcurl.so.4` or re-ship the desktop typo — re-apply both. Build recipe + the OpenSSL-1.1 curl are reproducible from `/tmp/curl-build` notes. Related: [[instamat-bake-to-disk]].
