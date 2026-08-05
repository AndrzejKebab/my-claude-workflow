---
name: env-numpy-opencv-constraints
description: ComfyUI uv env — numpy must stay <2.4 and OpenCV must be a single headless-contrib variant
metadata: 
  node_type: memory
  type: project
  originSessionId: 0f7d1cd2-0ea1-47f4-b50f-d296dd22e60f
  modified: 2026-07-19T19:39:31.061Z
---

The venv (`/mnt/archive4/comfyui/.venv`) is a hybrid: a uv-managed core (pyproject.toml + uv.lock) plus many custom-node runtime deps (ultralytics, insightface, mediapipe, numba, onnxruntime-gpu, etc.) pip-installed **out-of-band** and NOT in the lock. `uv run --extra cu130` (via `run.sh`) leaves those extras in place, so they persist — but a bare `uv sync` would remove them and break nodes.

Two hard constraints, both enforced in pyproject.toml:
- **`numpy>=1.25.0,<2.4`** — numba (0.63.1, pulled by several custom nodes) supports numpy ≤ 2.3; numpy 2.4 hard-fails its import. Do not lift the cap until numba ships a 2.4-compatible release.
- **`opencv-contrib-python-headless>=4.10,<5`** — exactly ONE OpenCV variant. Custom-node requirements pin different variants (`opencv-python`, `opencv-python-headless`, `opencv-contrib-python`); they all clobber the same `cv2/` dir. A stale numpy-1 `opencv-python-headless==4.7.0.72` clobber caused a hard startup crash (`numpy.core.multiarray failed to import` on `import cv2`, cascading into ultralytics/mediapipe/insightface). `<5` keeps it off the OpenCV 5 major line these 4.x-era nodes aren't written for. If a re-run of a custom node's `requirements.txt` reintroduces a bare `opencv-python`, remove all variants + `rm -rf .venv/lib/python3.12/site-packages/cv2`, then `uv run --extra cu130` to reinstall the single locked build.

Always launch with `./run.sh` (uses `--extra cu130`). Never run a bare `uv run --project .` for one-offs — without the extra, uv re-resolves torch off the default index and starts pulling a whole CUDA-12 torch stack.
