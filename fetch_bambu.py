#!/usr/bin/env python3
"""Fetch Bambu Lab P2S local status (LAN MQTT) and push to Quote/0 as image."""
import os, sys, json, time, ssl, logging, base64, io, threading
from datetime import datetime
from typing import Optional, List
from PIL import Image, ImageDraw, ImageFont
import paho.mqtt.client as mqtt
import requests

import camera as _camera

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)


def _envbool(name: str, default: bool = False) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "on")


def _envint(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, "").strip() or default)
    except ValueError:
        return default


# ========== CONFIG (from environment, see .env) ==========
PRINTER_IP        = os.environ.get("PRINTER_IP", "").strip()
PRINTER_SN        = os.environ.get("PRINTER_SN", "").strip()
PRINTER_ACCESS    = os.environ.get("PRINTER_ACCESS", "").strip()
QUOTE0_API_KEY    = os.environ.get("QUOTE0_API_KEY", "").strip()
QUOTE0_DEVICE_ID  = os.environ.get("QUOTE0_DEVICE_ID", "").strip()
INTERVAL_SECONDS  = _envint("INTERVAL_SECONDS", 60)
SHOW_CAMERA       = _envbool("SHOW_CAMERA", True)
CAMERA_PROTO      = os.environ.get("CAMERA_PROTO", "auto").strip().lower()
HMS_IGNORE        = {c.strip().upper() for c in os.environ.get("HMS_IGNORE", "").split(",") if c.strip()}
_last_suppressed: set = set()

_missing = [k for k, v in {
    "PRINTER_IP": PRINTER_IP, "PRINTER_SN": PRINTER_SN, "PRINTER_ACCESS": PRINTER_ACCESS,
    "QUOTE0_API_KEY": QUOTE0_API_KEY, "QUOTE0_DEVICE_ID": QUOTE0_DEVICE_ID,
}.items() if not v]
if _missing:
    log.warning("Missing env vars: %s", ", ".join(_missing))
# =========================================================

W, H = 296, 152
QUOTE0_BASE = "https://dot.mindreset.tech/api/authV2/open/device"

state = {"data": None, "lock": threading.Lock(), "connected": False}


def _to_float(v, default: float = 0.0) -> float:
    """Tolerant float coercion. Some firmware sends temps as strings."""
    if v is None or v == "":
        return default
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _deep_merge(dst: dict, src: dict) -> None:
    """Recursive dict merge. Required for P1 series — printer sends partial
    incremental updates after pushall, and a shallow update would wipe
    nested objects like `ams` when only one of its keys changes."""
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _deep_merge(dst[k], v)
        else:
            dst[k] = v


def on_connect(client, userdata, flags, rc, properties=None):
    log.info("MQTT connected rc=%s", rc)
    state["connected"] = True
    client.subscribe(f"device/{PRINTER_SN}/report")
    client.publish(
        f"device/{PRINTER_SN}/request",
        json.dumps({"pushing": {"sequence_id": "0", "command": "pushall"}}),
    )


def on_disconnect(client, userdata, *args, **kwargs):
    log.warning("MQTT disconnected")
    state["connected"] = False


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return
    print_obj = payload.get("print")
    if not print_obj:
        return
    with state["lock"]:
        if state["data"] is None:
            state["data"] = {}
        _deep_merge(state["data"], print_obj)


def start_mqtt() -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="quote0_bambu", protocol=mqtt.MQTTv311)
    client.username_pw_set("bblp", PRINTER_ACCESS)
    client.tls_set(cert_reqs=ssl.CERT_NONE)
    client.tls_insecure_set(True)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.reconnect_delay_set(min_delay=2, max_delay=30)
    client.connect_async(PRINTER_IP, 8883, keepalive=60)
    client.loop_start()
    return client


def grab_camera_frame() -> Optional[Image.Image]:
    return _camera.grab_camera_frame(PRINTER_IP, PRINTER_ACCESS, CAMERA_PROTO)


def fmt_eta(minutes) -> str:
    try:
        m = int(minutes)
    except (TypeError, ValueError):
        return "--"
    if m <= 0:
        return "--"
    h, mm = divmod(m, 60)
    return f"{h}h{mm:02d}m" if h else f"{mm}m"


def draw_bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, pct: float):
    draw.rectangle([x, y, x + w, y + h], outline="black")
    fill = int(w * max(0.0, min(float(pct), 100.0)) / 100.0)
    if fill > 0:
        draw.rectangle([x, y, x + fill, y + h], fill="black")


def load_fonts():
    # Debian apt: fonts-dejavu-core → /usr/share/fonts/truetype/dejavu/
    # Alpine apk: font-dejavu       → /usr/share/fonts/dejavu/
    for base in ("/usr/share/fonts/truetype/dejavu",
                 "/usr/share/fonts/dejavu"):
        try:
            return (
                ImageFont.truetype(f"{base}/DejaVuSans-Bold.ttf", 13),  # ft
                ImageFont.truetype(f"{base}/DejaVuSans.ttf", 11),        # fm
                ImageFont.truetype(f"{base}/DejaVuSans.ttf", 10),        # fs
            )
        except OSError:
            continue
    d = ImageFont.load_default()
    return d, d, d


def cover_resize(img: Image.Image, tw: int, th: int) -> Image.Image:
    """Resize preserving aspect ratio, center-crop to (tw, th)."""
    sr = img.width / img.height
    dr = tw / th
    if sr > dr:
        nw = int(img.height * dr)
        x0 = (img.width - nw) // 2
        img = img.crop((x0, 0, x0 + nw, img.height))
    elif sr < dr:
        nh = int(img.width / dr)
        y0 = (img.height - nh) // 2
        img = img.crop((0, y0, img.width, y0 + nh))
    return img.resize((tw, th), Image.LANCZOS)


SPEED_LABEL = {1: "Silent", 2: "Std", 3: "Sport", 4: "Ludi"}


def _active_tray_idx(d: dict) -> int:
    """Active tray global index (ams_id*4 + slot). Prefers V2 protocol's
    `device.extruder.info[].snow` (bits 15:8 = ams_id, 7:0 = slot) used by
    P2S/H2 series; falls back to legacy `ams.tray_now`. Returns 254 for
    external spool, -1 for unknown."""
    info = ((d.get("device") or {}).get("extruder") or {}).get("info")
    if isinstance(info, list):
        for ext in info:
            if not isinstance(ext, dict):
                continue
            snow = ext.get("snow")
            if isinstance(snow, int) and 0 <= snow < 0xFFFF:
                ams_id = (snow >> 8) & 0xFF
                slot = snow & 0xFF
                if slot == 0xFE or ams_id == 0xFE:
                    return 254
                if ams_id == 0xFF or slot == 0xFF:
                    continue
                return ams_id * 4 + slot
    raw = (d.get("ams") or {}).get("tray_now")
    try:
        return int(raw) if raw is not None else -1
    except (TypeError, ValueError):
        return -1


def _tray_grid_label(ams_id: int, slot: int) -> str:
    """AMS HT (single-tray unit) reports ams_id >= 128. Render as H{n}
    instead of overflowing the T{n} grid."""
    if ams_id >= 128:
        return f"H{ams_id - 127}"
    return f"T{ams_id * 4 + slot + 1}"


def _chamber_temp(d: dict) -> Optional[float]:
    """X1C / X1E / H2D report `chamber_temper` at the top level. P2S keeps
    the same sensor under `device.ctc.info.temp` (integer °C). Probe both."""
    v = d.get("chamber_temper")
    if v is None:
        v = (((d.get("device") or {}).get("ctc") or {}).get("info") or {}).get("temp")
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _right_nozzle_temp(d: dict) -> Optional[float]:
    """H2D dual-extruder right nozzle temperature; field name varies by
    firmware. Returns None on single-nozzle machines."""
    for key in ("right_nozzle_temper", "secondary_nozzle_temper",
                "second_nozzle_temper", "tool1_nozzle_temper"):
        v = d.get(key)
        if v is not None:
            f = _to_float(v, -1)
            if f >= 0:
                return f
    info = ((d.get("device") or {}).get("extruder") or {}).get("info")
    if isinstance(info, list) and len(info) >= 2 and isinstance(info[1], dict):
        v = info[1].get("temp")
        if v is not None:
            f = _to_float(v, -1)
            if f >= 0:
                return f
    return None


def tray_label(d: dict) -> str:
    n = _active_tray_idx(d)
    if n == 254:
        return "Ext"
    if n < 0:
        return ""
    ams_id, slot = divmod(n, 4)
    return _tray_grid_label(ams_id, slot)


def get_trays(d: dict) -> list:
    """Flatten AMS units into per-tray dicts."""
    ams = d.get("ams") or {}
    active_idx = _active_tray_idx(d)
    out = []
    for unit in ams.get("ams") or []:
        try:
            ams_id = int(unit.get("id", 0))
        except (TypeError, ValueError):
            ams_id = 0
        for t in unit.get("tray", []) or []:
            try:
                tid = int(t.get("id", 0))
            except (TypeError, ValueError):
                tid = 0
            gidx = ams_id * 4 + tid
            ttype = (t.get("tray_type") or "").strip()
            color = (t.get("tray_color") or "").strip()
            try:
                remain = int(t.get("remain") if t.get("remain") is not None else -1)
            except (TypeError, ValueError):
                remain = -1
            out.append({
                "idx": gidx,
                "label": _tray_grid_label(ams_id, tid),
                "type": ttype or "-",
                "color": color,
                "remain": remain,
                "active": gidx == active_idx,
                "empty": not ttype,
            })
    return out


def get_ams_unit_info(d: dict):
    """Return (humidity_level 0-5, humidity_pct or None, temp_str) from
    first AMS unit. `humidity` is a 1-5 level (driest..wettest).
    `humidity_raw` is true %, also mapped to 5 buckets when present."""
    units = (d.get("ams") or {}).get("ams")
    if not units:
        return 0, None, ""
    u = units[0]
    h_lvl_raw = str(u.get("humidity", "")).strip()
    h_raw = u.get("humidity_raw")
    t_str = str(u.get("temp", "")).strip()
    level = 0
    pct: Optional[int] = None
    if h_raw not in (None, "", "0"):
        try:
            f = float(h_raw)
            pct = int(round(f))
            level = min(5, max(1, int(f // 20) + 1))
        except (TypeError, ValueError):
            pass
    if not level and h_lvl_raw:
        try:
            level = max(0, min(5, int(h_lvl_raw)))
        except ValueError:
            pass
    return level, pct, t_str


def draw_drops(draw: ImageDraw.ImageDraw, x: int, y: int, level: int, total: int = 5,
               drop_w: int = 5, drop_h: int = 7, gap: int = 1) -> int:
    """Draw `total` teardrop shapes (pointed top, rounded bottom).
    First `level` are filled, the rest hollow. Returns end x."""
    for i in range(total):
        cx = x + i * (drop_w + gap)
        pts = [
            (cx + 2, y),                  # tip
            (cx + drop_w - 1, y + 3),
            (cx + drop_w - 1, y + 5),
            (cx + 2, y + drop_h - 1),     # bottom
            (cx, y + 5),
            (cx, y + 3),
        ]
        if i < level:
            draw.polygon(pts, fill="black")
        else:
            draw.polygon(pts, outline="black")
    return x + total * (drop_w + gap)


def color_swatch(color_hex: str, size: int = 7) -> Image.Image:
    """Hex like 'F95959FF' -> 1-bit dithered grayscale swatch."""
    gray = 200
    if color_hex and len(color_hex) >= 6:
        try:
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            gray = int(0.299 * r + 0.587 * g + 0.114 * b)
        except ValueError:
            pass
    sw = Image.new("L", (size, size), gray)
    return sw.convert("1", dither=Image.FLOYDSTEINBERG)


# --------- HMS error code lookup (Bambu public table) ---------
HMS_DB_URL = "https://e.bambulab.com/query.php"
HMS_CACHE_PATH = "/tmp/bambu_hms.json"
HMS_DB = {}  # "ECODE16HEX" -> "description"


def load_hms_db():
    global HMS_DB
    raw = None
    try:
        r = requests.get(HMS_DB_URL, params={"lang": "en", "f": "hms"}, timeout=15)
        r.raise_for_status()
        raw = r.json()
        try:
            with open(HMS_CACHE_PATH, "w") as f:
                json.dump(raw, f)
        except OSError:
            pass
    except Exception as e:
        log.warning("HMS fetch failed (%s); trying cache", e)
        try:
            with open(HMS_CACHE_PATH) as f:
                raw = json.load(f)
        except Exception:
            return
    items = ((raw or {}).get("data", {}).get("device_hms", {}) or {}).get("en", []) or []
    HMS_DB = {
        str(it.get("ecode", "")).upper(): it.get("intro", "")
        for it in items if it.get("ecode") and it.get("intro")
    }
    log.info("HMS db loaded: %d entries", len(HMS_DB))


def hms_describe(h: dict):
    try:
        attr = int(h.get("attr", 0))
        code = int(h.get("code", 0))
    except (TypeError, ValueError):
        return "HMS_?", ""
    ecode = f"{attr:08X}{code:08X}"
    return ecode, HMS_DB.get(ecode, "")


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_w: int):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w).strip()
        try:
            wlen = draw.textlength(cand, font=font)
        except AttributeError:
            wlen = len(cand) * 6
        if wlen <= max_w:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def hms_lines(hms_list) -> List[str]:
    """Best-effort HMS error rendering. hms_list is a list of dicts with attr/code keys."""
    out = []
    for h in (hms_list or [])[:3]:
        attr = h.get("attr", 0) or 0
        code = h.get("code", 0) or 0
        try:
            tag = f"HMS_{int(attr):08X}_{int(code):08X}"
        except (TypeError, ValueError):
            tag = "HMS error"
        out.append(tag)
    return out


def render_image(d: dict) -> str:
    img = Image.new("1", (W, H), 1)
    draw = ImageDraw.Draw(img)
    ft, fm, fs = load_fonts()

    global _last_suppressed
    all_hms = d.get("hms") or []
    visible_hms = [h for h in all_hms
                   if f"{h.get('attr',0):08X}{h.get('code',0):08X}" not in HMS_IGNORE]
    suppressed = {f"{h.get('attr',0):08X}{h.get('code',0):08X}" for h in all_hms
                  if f"{h.get('attr',0):08X}{h.get('code',0):08X}" in HMS_IGNORE}
    if suppressed != _last_suppressed:
        if suppressed:
            log.info("HMS suppressed by HMS_IGNORE: %s", ",".join(sorted(suppressed)))
        elif _last_suppressed:
            log.info("HMS_IGNORE entries cleared on printer side: %s",
                     ",".join(sorted(_last_suppressed)))
        _last_suppressed = suppressed
    if visible_hms:
        return _render_hms(img, draw, ft, fm, fs, {**d, "hms": visible_hms})

    cam = None
    if SHOW_CAMERA:
        cam = grab_camera_frame()
    if cam is not None:
        return _render_with_camera(img, draw, ft, fm, fs, d, cam)
    return _render_data_only(img, draw, ft, fm, fs, d)


def _render_hms(img, draw, ft, fm, fs, d):
    draw.rectangle([0, 0, W, 18], fill="black")
    draw.text((4, 1), "P2S  ALERT", font=ft, fill="white")
    draw.text((W - 76, 4), datetime.now().strftime("%m-%d %H:%M"), font=fs, fill="white")
    draw.rectangle([0, 0, W - 1, H - 1], outline="black")

    y = 21
    for h in (d.get("hms") or []):
        if y > H - 14:
            break
        ecode, desc = hms_describe(h)
        draw.text((4, y), ecode, font=fs, fill="black")
        y += 11
        if desc:
            for line in wrap_text(draw, desc, fs, W - 12)[:3]:
                if y > H - 14:
                    break
                draw.text((10, y), line, font=fs, fill="black")
                y += 11
        y += 2

    stage = d.get("gcode_state") or ""
    draw.text((4, H - 12), f"State: {stage}", font=fs, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _render_with_camera(img, draw, ft, fm, fs, d, cam):
    stage = (d.get("gcode_state") or "?")
    pct = d.get("mc_percent") or 0
    eta = d.get("mc_remaining_time")
    nozzle = _to_float(d.get("nozzle_temper"))
    nozzle2 = _right_nozzle_temp(d)
    bed = _to_float(d.get("bed_temper"))
    chamber_f = _chamber_temp(d)
    layer = d.get("layer_num")
    total_layer = d.get("total_layer_num")
    name = d.get("subtask_name") or d.get("gcode_file") or ""
    spd = d.get("spd_lvl")
    trays = get_trays(d)

    HEADER_H, BOTTOM_H = 16, 24
    CAM_W = 200
    CAM_H = H - HEADER_H - BOTTOM_H
    RIGHT_X = CAM_W + 4

    cam = cam.convert("L")
    cam = cover_resize(cam, CAM_W, CAM_H)
    cam = cam.convert("1", dither=Image.FLOYDSTEINBERG)
    img.paste(cam, (0, HEADER_H))

    draw.rectangle([0, 0, W, HEADER_H - 1], fill="white")
    draw.text((4, 1), f"P2S  {stage}", font=ft, fill="black")
    right_hdr = f"{pct}%  {datetime.now().strftime('%H:%M')}"
    draw.text((W - 76, 2), right_hdr, font=fs, fill="black")
    draw.line([(0, HEADER_H - 1), (W, HEADER_H - 1)], fill="black")

    draw.rectangle([CAM_W, HEADER_H, W, H - BOTTOM_H], fill="white")
    rx = RIGHT_X
    ry = HEADER_H + 1

    if nozzle2 is not None:
        draw.text((rx, ry), f"N1 {nozzle:.0f}°  N2 {nozzle2:.0f}°", font=fs, fill="black")
        ry += 11
        chamber_str = f"  C{chamber_f:.0f}°" if chamber_f is not None else ""
        draw.text((rx, ry), f"B{bed:.0f}°{chamber_str}", font=fs, fill="black")
        ry += 11
    else:
        chamber_str = f" C{chamber_f:.0f}°" if chamber_f is not None else ""
        draw.text((rx, ry), f"N{nozzle:.0f}° B{bed:.0f}°{chamber_str}", font=fs, fill="black")
        ry += 11

    h_level, h_pct, t_str = get_ams_unit_info(d)
    # Row 1: AMS internal temp (with label).
    if t_str:
        draw.text((rx, ry), f"AMS  {_to_float(t_str):.0f}°", font=fs, fill="black")
        ry += 11
    # Row 2: humidity drops + %, indented under the AMS label above.
    if h_level or h_pct is not None:
        x_after = rx
        if h_level:
            x_after = draw_drops(draw, x_after, ry + 3, h_level) + 4
        if h_pct is not None:
            draw.text((x_after, ry), f"{h_pct}%", font=fs, fill="black")
        ry += 11

    draw.line([(rx, ry), (W - 4, ry)], fill="black"); ry += 3

    if trays:
        for tr in trays[:4]:
            sw = color_swatch(tr["color"])
            img.paste(sw, (rx, ry + 1))
            draw.rectangle([rx - 1, ry, rx + 7, ry + 8], outline="black")
            mark = "*" if tr["active"] else " "
            ttype = tr["type"] if not tr["empty"] else "—"
            prefix = f"{tr['label']}{mark} {ttype[:5]}"
            draw.text((rx + 10, ry), prefix, font=fs, fill="black")
            if tr["remain"] >= 0 and not tr["empty"]:
                pct_text = f"{tr['remain']}%"
                try:
                    pw = int(draw.textlength(pct_text, font=fs))
                except AttributeError:
                    pw = len(pct_text) * 6
                draw.text((W - 4 - pw, ry), pct_text, font=fs, fill="black")
            ry += 11
    else:
        draw.text((rx, ry), "Ext spool", font=fs, fill="black"); ry += 11
        if spd in SPEED_LABEL:
            draw.text((rx, ry), f"Spd {SPEED_LABEL[spd]}", font=fs, fill="black")
            ry += 11

    ry += 2
    draw.line([(rx, ry), (W - 4, ry)], fill="black"); ry += 3
    if eta:
        draw.text((rx, ry), f"ETA {fmt_eta(eta)}", font=fs, fill="black"); ry += 11
    if layer and total_layer:
        draw.text((rx, ry), f"L{layer}/{total_layer}", font=fs, fill="black")

    by = H - BOTTOM_H
    draw.line([(0, by), (W, by)], fill="black")
    short = name if len(name) <= 32 else name[:30] + ".."
    draw.text((4, by + 3), short, font=fs, fill="black")
    bar_y = by + 16
    draw_bar(draw, 4, bar_y, 256, 6, pct)
    draw.text((266, bar_y - 4), f"{pct}%", font=fs, fill="black")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _render_data_only(img, draw, ft, fm, fs, d):
    stage = (d.get("gcode_state") or "?")
    pct = d.get("mc_percent") or 0
    eta = d.get("mc_remaining_time")
    nozzle = _to_float(d.get("nozzle_temper"))
    nozzle2 = _right_nozzle_temp(d)
    bed = _to_float(d.get("bed_temper"))
    chamber_f = _chamber_temp(d)
    layer = d.get("layer_num")
    total_layer = d.get("total_layer_num")
    name = d.get("subtask_name") or d.get("gcode_file") or ""
    spd = d.get("spd_lvl")
    tray = tray_label(d)

    y = 2
    draw.text((6, y), f"P2S  {stage}", font=ft, fill="black")
    draw.text((230, y + 2), datetime.now().strftime("%H:%M"), font=fs, fill="black")
    y += 18
    if name:
        short = name if len(name) < 38 else name[:35] + "..."
        draw.text((6, y), short, font=fs, fill="black")
    y += 14
    draw.text((6, y), f"Progress  {pct}%", font=fm, fill="black")
    if layer and total_layer:
        draw.text((180, y), f"L {layer}/{total_layer}", font=fs, fill="black")
    y += 14
    draw_bar(draw, 6, y, 284, 8, pct)
    y += 14
    if nozzle2 is not None:
        draw.text((6, y), f"N1 {nozzle:.0f}°", font=fm, fill="black")
        draw.text((78, y), f"N2 {nozzle2:.0f}°", font=fm, fill="black")
        draw.text((148, y), f"B {bed:.0f}°", font=fm, fill="black")
    else:
        draw.text((6, y), f"N {nozzle:.0f}°", font=fm, fill="black")
        draw.text((78, y), f"B {bed:.0f}°", font=fm, fill="black")
        if chamber_f is not None:
            draw.text((148, y), f"C {chamber_f:.0f}°", font=fm, fill="black")
    extras = []
    if tray:
        extras.append(tray)
    if spd in SPEED_LABEL:
        extras.append(SPEED_LABEL[spd])
    if extras:
        draw.text((220, y), "  ".join(extras), font=fs, fill="black")
    y += 14
    draw.text((6, y), f"ETA  {fmt_eta(eta)}", font=fm, fill="black")
    y += 14
    trays = get_trays(d)
    if trays:
        x = 6
        for tr in trays[:4]:
            label = f"{tr['label']}{'*' if tr['active'] else ''}"
            ttype = tr["type"] if not tr["empty"] else "—"
            draw.text((x, y), f"{label} {ttype[:5]}", font=fs, fill="black")
            x += 72
    draw.text((220, H - 12), datetime.now().strftime("%m-%d %H:%M"), font=fs, fill="black")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def render_status_image(title: str, lines: List[str]) -> str:
    img = Image.new("1", (W, H), 1)
    draw = ImageDraw.Draw(img)
    ft, fm, _ = load_fonts()
    draw.text((8, 16), title, font=ft, fill="black")
    y = 44
    for line in lines:
        draw.text((8, y), line, font=fm, fill="black")
        y += 16
    draw.text((220, H - 14), datetime.now().strftime("%m-%d %H:%M"), font=fm, fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def push_image(image_b64: str):
    r = requests.post(
        f"{QUOTE0_BASE}/{QUOTE0_DEVICE_ID}/image",
        json={"refreshNow": True, "image": image_b64, "border": 0, "ditherType": "NONE"},
        headers={"Authorization": f"Bearer {QUOTE0_API_KEY}", "Content-Type": "application/json"},
        timeout=30,
    )
    if not r.ok:
        log.error("Quote/0 HTTP %s: %s", r.status_code, r.text[:300])
    r.raise_for_status()
    log.info("Quote/0: %s", r.json())


if __name__ == "__main__":
    log.info("Starting bambu loop ip=%s sn=%s interval=%ds camera=%s",
             PRINTER_IP, PRINTER_SN[:6] + "..." if PRINTER_SN else "<unset>",
             INTERVAL_SECONDS, SHOW_CAMERA)
    load_hms_db()
    client = start_mqtt()
    # Wait briefly for MQTT to connect and the first pushall to arrive,
    # otherwise the first render races ahead and pushes "MQTT connecting..."
    # to Quote/0 — and with INTERVAL_SECONDS=300 the user stares at it 5min.
    deadline = time.time() + 15
    while time.time() < deadline:
        with state["lock"]:
            ready = state["data"] is not None
        if ready:
            break
        time.sleep(0.5)
    while True:
        try:
            with state["lock"]:
                d = dict(state["data"]) if state["data"] else None
            if d is None:
                msg = "MQTT connecting..." if not state["connected"] else "Waiting first push..."
                push_image(render_status_image("P2S Offline", [msg, f"Host {PRINTER_IP or '?'}"]))
            else:
                push_image(render_image(d))
        except Exception:
            log.exception("Loop error")
        time.sleep(INTERVAL_SECONDS)
