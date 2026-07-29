# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Single-purpose Python service: subscribes to a Bambu Lab printer's **local** MQTT broker, optionally grabs a camera frame, renders a 296×152 1-bit image, and POSTs it to a Quote/0 e-paper device. One Docker container, `restart: always`. Sister project to `../quote_cc` (same Quote/0 push contract, different data source).

Baseline target is P2S, but the code handles a fleet: **P1P/P1S, A1/A1 mini, X1/X1C/X1E, H2D/H2DPro**. Model differences (camera protocol, V2 active-tray, dual nozzle, AMS HT, string-typed temps, P1 incremental-push merge) are all handled in one codebase — see README.md "支持机型".

## Common commands

```bash
# Offline render loop — no printer, no network, ~1s. THE primary dev loop.
python3 preview.py            # image-mode layout  -> preview_*.png
python3 preview_canvas.py     # canvas-mode layout -> canvas_*.png
open preview_camera_x3.png    # then Read the _x3.png to verify visually

# Run in Docker (prod): pulls prebuilt multi-arch image from GHCR
cp .env.example .env          # fill in 5 required values
docker compose up -d
docker compose logs -f

# Local-dev container: bind-mounts sources + inline-installs deps
docker compose --profile dev up bambu_cc_dev
```

There are no unit tests and no linter configured. `preview.py` is the verification harness: it monkeypatches `fb.SHOW_CAMERA` / `fb.grab_camera_frame` / `fb.HMS_DB` and calls `render_image()` with mock dicts that mirror the real `pushall` report shape. Editing a `_render_*` function → rerun `preview.py` → Read the regenerated `_x3.png`. **Keep the mock data in `preview.py` in sync** with any new report field you start reading.

## Files

- `fetch_bambu.py` — main script (~700 lines): config, MQTT, all `_render_*` (image) paths, `render_canvas_window` (canvas dispatch), Quote/0 POST, the `__main__` loop.
- `camera.py` — camera grab, split out by protocol (see below). `fetch_bambu.grab_camera_frame()` is a thin wrapper over `camera.grab_camera_frame()`.
- `quote0_canvas.py` — Canvas API path: builds a `div`/`span`/`img` element tree (`build_window_camera` / `_hms` / `_status`) and POSTs to `/device/<id>/canvas`. Reuses fetch_bambu's data-extraction helpers; only the camera frame and tray swatches are `<img>` (the rest is CSS).
- `preview.py` — offline render harness for the image layout → `preview_*.png` (+ `_x3`).
- `preview_canvas.py` — offline harness for the canvas layout → `canvas_*.png` (+ `_x3`). Approximate (Arial vs device pixel font); use for positioning, not pixel fidelity.
- `Dockerfile` — multi-stage: copies a static ffmpeg binary from `mwader/static-ffmpeg:7.1` into `python:3.12-alpine`, apk-installs `font-dejavu` + `tzdata`. ~230MB.
- `docker-compose.yml` — `bambu_cc` pulls `ghcr.io/aiaid/quote_bambu:latest`; `bambu_cc_dev` (profile `dev`) bind-mounts source for iteration.
- `.github/workflows/docker-publish.yml` — per-arch build (amd64 + arm64 runners) → push-by-digest to GHCR → merge into a manifest list, mirrored to Docker Hub if `DOCKERHUB_USERNAME`/`_TOKEN` secrets are set.
- `.env.example` → copy to `.env` (gitignored).

## How data flows

1. `start_mqtt()` connects `mqtts://<PRINTER_IP>:8883` as user `bblp`, password = LAN access code. TLS validation disabled (`tls_insecure_set(True)`). Subscribes `device/<SN>/report`, publishes a `pushall` request.
2. `on_message` **deep-merges** each incoming `print` object into `state["data"]` under `state["lock"]`. The merge is recursive (`_deep_merge`) — required because P1-series firmware sends partial incremental updates after the initial `pushall`, and a shallow update would wipe nested objects like `ams`.
3. `__main__` waits up to 15s for the first push to land (so the first frame isn't a useless "MQTT connecting…" placeholder), then loops every `INTERVAL_SECONDS`:
   - Snapshot under lock: `d = dict(state["data"])`.
   - `PUSH_MODE` picks the transport (default `canvas`):
     - **canvas**: `render_canvas_window(d)` → `_canvas.push_window(...)` POSTs an element tree to `/device/<id>/canvas`. Dispatch: visible HMS → `build_window_hms`; else `build_window_camera` (camera frame omitted ⇒ empty box when no `SHOW_CAMERA`/grab fails).
     - **image**: `render_image(d)` returns a base64 PNG → `push_image()` POSTs to `/device/<id>/image`. Dispatch: visible HMS → `_render_hms`; else `SHOW_CAMERA` + frame → `_render_with_camera`; else `_render_data_only`.
   - HMS filtering (`HMS_IGNORE` + suppression logging) is shared via `_visible_hms(d)`; both paths call it.
4. `load_hms_db()` runs once at startup: fetches Bambu's public HMS table, caches to `/tmp/bambu_hms.json`, falls back to cache on failure.

## Camera (`camera.py`) — two protocols

`grab_camera_frame(ip, access, proto)` dispatches on `CAMERA_PROTO`:
- `rtsps` — `rtsps://bblp:<access>@<ip>:322/streaming/live/1` via **ffmpeg** subprocess (P2S, X1, H2). ~5–10s per frame.
- `jpeg` — raw TLS socket to **port 6000**: send 80-byte auth (`<IIII` magic + 32-byte user + 32-byte pwd), read 16-byte frame header, then JPEG payload, validate SOI/EOI (P1, A1). ~1–2s.
- `auto` (default) — probe port 322; if open, try RTSPS, else fall back to JPEG/6000.

ffmpeg uses `-rtsp_transport tcp` only — the old `-tls_verify 0` flag was removed (ffmpeg 7.1 in the slim/static build rejects it).

## Multi-model field handling (in `fetch_bambu.py`)

These helpers paper over firmware differences — read them before touching render code:
- `_active_tray_idx` — prefers V2 `device.extruder.info[].snow` (bits 15:8 = ams_id, 7:0 = slot, used by P2S/H2); falls back to legacy `ams.tray_now`. Returns 254 for external spool, -1 unknown.
- `_tray_grid_label` — AMS HT (single-tray unit) reports `ams_id >= 128`; rendered as `H{n}` instead of overflowing the `T{n}` grid.
- `_chamber_temp` — top-level `chamber_temper` (X1/H2D) or `device.ctc.info.temp` (P2S).
- `_right_nozzle_temp` — H2D dual extruder; tries several field names + `extruder.info[1].temp`. Returns None on single-nozzle machines (→ single temp line).
- `_to_float` — some firmware sends temps as strings; coerce tolerantly.
- `get_ams_unit_info` — humidity is a 1–5 level (driest→wettest); `humidity_raw` is true % and gets bucketed into the same 5 levels when present.

## Layout (296×152, 1-bit)

Camera mode is default. Header 16px / cam-left 200×112 / right-column 96×112 (`RIGHT_X = 204`) / bottom 24px.

Right column top→bottom: temps line (`N…° B…° C…°`, or `N1/N2` + `B/C` two lines on H2D) → AMS internal temp → humidity teardrops + % → separator → up to 4 tray rows (7×7 dithered swatch + bordered + `T{n}{*?} {type[:5]} {remain}%`) → separator → ETA + `L{layer}/{total}`. Bottom strip: filename (32-char truncate) + 256-wide progress bar + `%`.

HMS view (`_render_hms`): black header bar + per-error ecode + wrapped English description (from the public table) + `gcode_state`.

## Conventions & invariants — things not to break

- **No config file** — everything via env vars. Missing required vars warn (don't crash), so `preview.py` works without them. `_envbool`/`_envint` parse leniently.
- **Python 3.10+ compatible.** Security-supported dependency releases require
  Python 3.10 or newer. Keep CI green on both 3.10 and the production runtime's
  Python 3.12.
- **Render helpers take `(img, draw, ft, fm, fs, d)`** so they're driveable from `preview.py`. Fonts: `ft`=13pt bold, `fm`=11pt, `fs`=10pt.
- **Lock discipline** — main loop snapshots `dict(state["data"])` under `state["lock"]` before rendering; never render off the live dict.
- **paho v2 callback API** (`CallbackAPIVersion.VERSION2`) — `on_connect` has 5 args (`client, userdata, flags, rc, properties`).
- **HMS ecode format** — `f"{attr:08X}{code:08X}"` (uppercase, 16 hex, no separator). `HMS_IGNORE` matches this exact form to suppress benign/persistent warnings from full-screening; suppression changes are logged once (`_last_suppressed` dedup).
- **Font path is dual-probed** — `/usr/share/fonts/truetype/dejavu` (Debian apt) **and** `/usr/share/fonts/dejavu` (Alpine apk). Falls back to PIL bitmap default (the macOS `preview.py` case).
- Don't add report fields just because they exist — README has the curated set.

## Env vars (.env)

5 required: `PRINTER_IP`, `PRINTER_SN`, `PRINTER_ACCESS` (8-digit LAN code), `QUOTE0_API_KEY`, `QUOTE0_DEVICE_ID`.
Behavior: `INTERVAL_SECONDS` (60), `SHOW_CAMERA` (true), `CAMERA_PROTO` (auto/rtsps/jpeg), `HMS_IGNORE` (comma-sep ecodes), `TZ` (Asia/Shanghai recommended — container defaults to UTC).

## Access notes (P2S baseline)

- **No Developer/LAN-only Mode needed for read-only access** on P2S/P1/X1/A1. In cloud mode, ports 8883 (MQTT) and 322 (RTSPS) stay open on the LAN to anyone with the access code. The 2025 Authorization Control gates *write* commands, not status-push subscription — so Quote/0 + the Handy app coexist.
- **H2D/H2DPro exception**: they do **not** expose local MQTT in cloud mode → require LAN-only + Developer Mode, which disables the cloud Handy app. Single-printer trade-off; doesn't affect P2S.

## Reference

- `../quote_cc/fetch_usage.py` — sibling project; same Quote/0 image POST contract, different render. Reference for the push API.
- [OpenBambuAPI (Doridian)](https://github.com/Doridian/OpenBambuAPI) — de facto MQTT/RTSP/HTTP/TLS doc; trust over guesswork.
- [PrintSphere (cptkirki)](https://github.com/cptkirki/PrintSphere) — ESP32 reference, V2 protocol fields.
