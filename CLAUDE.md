# CLAUDE.md

Project context for Claude Code working in this directory.

## What this is

Single-purpose Python script that subscribes to a Bambu Lab P2S printer's local MQTT broker, optionally grabs an RTSPS camera frame, renders a 296×152 1-bit image, and POSTs it to a Quote/0 e-paper device. Runs in a single Docker container with `restart: always`. Sister project to `../quote_cc` (same Quote/0 push pattern, different data source).

## Files

- `fetch_bambu.py` — main script. ~600 lines. Three render paths (camera / data-only / HMS alert) sharing helpers
- `docker-compose.yml` — uses `python:3.12-slim`, inline-installs ffmpeg + paho-mqtt + requests + pillow on first run
- `.env.example` → copy to `.env` (gitignored). Holds 5 secrets/IDs; script aborts soft (warn) if missing
- `preview.py` — offline render with mock data, produces `preview_*.png` (real size) and `preview_*_x3.png` (3× for inspection)

## How data flows

1. `start_mqtt()` connects to `mqtts://<PRINTER_IP>:8883` user `bblp` password=LAN access code, subscribes `device/<SN>/report`, sends `pushall`. TLS validation disabled.
2. Background thread merges incoming `print` JSON into `state["data"]` under a lock
3. Main loop every `INTERVAL_SECONDS`:
   - If no data yet: render offline status image
   - If `hms` non-empty: `_render_hms` (full-screen alert)
   - Else if `SHOW_CAMERA`: `grab_camera_frame()` via ffmpeg → `_render_with_camera`
   - Else / camera fail: `_render_data_only`
   - POST to Quote/0 `/image` endpoint
4. `load_hms_db()` runs once at startup, caches Bambu's public HMS table to `/tmp/bambu_hms.json`

## Layout (296×152, 1-bit)

Camera mode is the default. Header 16 px / cam left 200×112 / right column 96×112 / bottom 24 px.

Right column (top → bottom):
1. Temps single line: `N215° B60° C32°` (font fs, 10pt)
2. AMS line: `AMS` text + 5 teardrop polygons (filled per humidity level 1–5) + AMS unit temp
3. Separator
4. Up to 4 tray rows: 7×7 dithered color swatch + bordered + `T{n}{*?} {type[:5]} {remain}%`
5. Separator
6. ETA + layer

Bottom strip: filename (32 char truncate) + 256-wide progress bar + `%`.

HMS view: black header bar + ecode + wrapped description (English, from public HMS table) + state.

## Conventions

- No external config file — everything via env vars (`os.environ`). Missing vars warn but don't crash, useful for `preview.py` dev loop.
- All rendering helpers take `draw, fonts, ...` so they can be unit-tested via `preview.py`.
- Mock data mirrors real `pushall` report structure (`ams.ams[].tray[]`, `ams.tray_now`, `hms[]`, etc.) — when adjusting render code, update mock to match.
- Don't add fields just because they're in the report — see README for the curated set.
- Python 3.10+ syntax (`X | None`) is **avoided** because `preview.py` runs against the user's macOS system Python 3.9. Use `Optional[X]` from `typing`.

## Iteration loop for layout tweaks

```bash
python3 preview.py    # ~1s, no network, no printer needed
open preview_camera_x3.png
```

If you change a render function, regenerate the previews and **read the `_x3.png` via the Read tool** to verify visually.

## Things not to break

- `state["lock"]` discipline — main loop does `dict(state["data"])` snapshot under lock before rendering
- `paho.mqtt.client` v2 callback API (`CallbackAPIVersion.VERSION2`) — the on_connect signature has 5 args
- `_envbool` / `_envint` lenient parsing for missing/empty env vars
- HMS table hex format: `f"{attr:08X}{code:08X}"` (uppercase, no separator)
- Fonts use absolute path `/usr/share/fonts/truetype/dejavu/...` — provided by `fonts-dejavu-core` apt package in compose. Falls back to PIL default if missing (preview script case on macOS uses PIL bitmap default).

## P2S notes

- V2 protocol — PrintSphere's `printer_client.cpp` confirms LAN MQTT topics/commands are unchanged from P1S/X1
- AMS field shape may differ slightly under V2 (`vir_slot` for filament info per PrintSphere README); current code uses common `ams.ams[].tray[]` structure
- Camera is 1920×1080 16:9 at port 322 RTSPS — confirmed at https://wiki.bambulab.com/en/p2s
- Printer must have Developer / LAN-only Mode toggled on in the screen UI, otherwise 8883/322 not exposed (post-2025 firmware Authorization Control)

## Related

- `../quote_cc/fetch_usage.py` — sibling project, Claude usage → Quote/0. Same push API, different render. Useful as a reference for the Quote/0 image POST contract.
- [OpenBambuAPI](https://github.com/Doridian/OpenBambuAPI) — de facto MQTT/RTSP/HTTP doc; trust this over guesswork
- [PrintSphere](https://github.com/cptkirki/PrintSphere) — ESP32 reference implementation, V2 fields
