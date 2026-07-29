"""Quote/0 Canvas API push — vector layout via div/span/CSS, image only where unavoidable.

The Image API (`/device/:id/image`) sends one flat PNG. The Canvas API
(`/device/:id/canvas`) sends a declarative element tree the device renders
server-side. We prefer Canvas: text / temps / trays / progress bar are drawn
with `div`/`span` + CSS so they stay crisp on the 1-bit panel, and ONLY the
camera frame — which is genuine pixels — falls back to an `<img>` carrying a
base64 PNG. (`build_window_full_image` keeps the whole-screen-PNG path around
as a fallback for when even that is preferable.)

Layout is rebuilt 1:1 against fetch_bambu._render_with_camera using absolute
positioning (position:relative root + position:absolute children) so element
coordinates match the pixel layout exactly rather than relying on flex.

Spec: https://dot.mindreset.tech/docs/service/open/canvas_api
  - windowData.default : array of element objects (required)
  - element            : {"type": "div"|"span"|"img", "props": {...}}
  - props.style        : CSS subset (position/top/left/width/height/px,
                         backgroundColor, border, fontSize..., NO z-index/calc)
  - img.props.src      : data URI or http(s) URL; .props.tw img-dither-*
  - text font classes  : props.tw "text-pixel-12-zpix" (pixel font, e-ink-friendly)
  - layoutFull         : {"tw":"p-0","style":{"padding":0}} for full-bleed 296x152
"""
import base64
import io
import logging
from datetime import datetime
from typing import List, Optional, Tuple

import requests

log = logging.getLogger(__name__)

W, H = 296, 152
QUOTE0_BASE = "https://dot.mindreset.tech/api/authV2/open/device"

BLACK = "#000"
WHITE = "#fff"
PIXEL_FONT = "text-pixel-12-zpix"  # crisp bitmap font; best on 1-bit e-ink

# Layout constants mirror fetch_bambu._render_with_camera.
HEADER_H, BOTTOM_H = 16, 24
CAM_W = 200
CAM_H = H - HEADER_H - BOTTOM_H  # 112
RIGHT_X = CAM_W + 4              # 204


# ---------- element-tree helpers ----------

def _el(t: str, style: dict, *, children=None, tw: Optional[str] = None,
        src: Optional[str] = None) -> dict:
    props: dict = {"style": style}
    if tw:
        props["tw"] = tw
    if src is not None:
        props["src"] = src
    if children is not None:
        props["children"] = children
    return {"type": t, "props": props}


def _abs(left, top, width=None, height=None, extra=None) -> dict:
    s = {"position": "absolute", "left": f"{left}px", "top": f"{top}px"}
    if width is not None:
        s["width"] = f"{width}px"
    if height is not None:
        s["height"] = f"{height}px"
    if extra:
        s.update(extra)
    return s


def _text(left, top, text, *, width=None, color=BLACK, align=None,
          ellipsis=False, font=PIXEL_FONT, height=11, line_h=11) -> dict:
    extra = {"color": color, "lineHeight": f"{line_h}px", "whiteSpace": "nowrap",
             "overflow": "hidden"}
    if ellipsis:
        extra["textOverflow"] = "ellipsis"
    if align:
        extra["textAlign"] = align
    return _el("span", _abs(left, top, width, height, extra),
               children=str(text), tw=font)


def _text_right(right, top, text, *, color=BLACK, font=PIXEL_FONT,
                height=11, line_h=11) -> dict:
    """Right-anchored text: positioned by its RIGHT edge (`right` px from the
    screen's right side) so values of different widths (e.g. "8%" vs "100%")
    line up on the right. textAlign:right on a shrink-wrapped span doesn't
    align across rows; anchoring via `right` does."""
    s = {"position": "absolute", "right": f"{right}px", "top": f"{top}px",
         "height": f"{height}px", "color": color, "lineHeight": f"{line_h}px",
         "whiteSpace": "nowrap", "textAlign": "right"}
    return {"type": "span", "props": {"style": s, "children": str(text), "tw": font}}


def _hline(left, top, width) -> dict:
    return _el("div", _abs(left, top, width, 1, {"backgroundColor": BLACK}))


def _png_data_uri(img) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _swatch_color(color_hex: str) -> str:
    """tray_color hex (e.g. F95959FF) -> a SOLID #000 or #fff for the swatch
    background. We binarize by luminance instead of handing the raw color to
    the device — mid grays dither into a faint pattern that's hard to read at
    9px, so a dark filament reads as a solid black block and a light one as a
    white block inside its border. Clearer than a dithered swatch."""
    if color_hex and len(color_hex) >= 6:
        try:
            r = int(color_hex[0:2], 16)
            g = int(color_hex[2:4], 16)
            b = int(color_hex[4:6], 16)
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            return WHITE if lum >= 150 else BLACK
        except ValueError:
            pass
    return WHITE


def _swatch_img(color_hex: str, size: int) -> str:
    """Dithered 1-bit swatch as a data URI, reusing fetch_bambu.color_swatch
    (same Floyd-Steinberg look as the Image-API path). The border is drawn by
    the <img> element's CSS, so render the fill at the inner size."""
    from PIL import Image  # lazy: PIL only needed when actually rendering
    import fetch_bambu as _fb
    inner = max(1, size - 2)
    sw = _fb.color_swatch(color_hex, inner).convert("L").resize((inner, inner),
                                                                Image.NEAREST)
    buf = io.BytesIO()
    sw.convert("1").save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def _bar(left, top, width, height, pct) -> dict:
    fill = int(width * max(0.0, min(float(pct), 100.0)) / 100.0)
    inner = []
    if fill > 0:
        inner.append(_el("div", {"position": "absolute", "left": "0px", "top": "0px",
                                 "height": "100%", "width": f"{fill}px",
                                 "backgroundColor": BLACK}, children=""))
    return _el("div", _abs(left, top, width, height,
                           {"border": "1px solid #000", "backgroundColor": WHITE,
                            "boxSizing": "border-box"}), children=inner)


def _drops(left, top, level, total=5, dot=6, gap=2) -> Tuple[List[dict], int]:
    """Humidity as small dots; first `level` filled (solid), rest hollow."""
    out = []
    for i in range(total):
        cx = left + i * (dot + gap)
        filled = i < level
        out.append(_el("div", _abs(cx, top, dot, dot, {
            "border": "1px solid #000",
            "borderRadius": "50%",
            "boxSizing": "border-box",
            "backgroundColor": BLACK if filled else WHITE,
        })))
    return out, left + total * (dot + gap)


# ---------- full-screen image fallback (kept) ----------

def build_window_full_image(image_b64: str, dither: str = "none") -> dict:
    """Whole rendered PNG in one full-screen <img>. Fallback path."""
    return {"default": [_el("img",
            {"width": f"{W}px", "height": f"{H}px"},
            src=f"data:image/png;base64,{image_b64}",
            tw=f"img-dither-{dither}")]}


# ---------- vector camera layout ----------

def build_window_camera(d: dict, cam_img, fb) -> dict:
    """Rebuild _render_with_camera as a Canvas element tree. `fb` is the
    fetch_bambu module (reused for its data-extraction helpers); `cam_img` is
    the grabbed PIL frame (or None)."""
    stage = d.get("gcode_state") or "?"
    pct = d.get("mc_percent") or 0
    eta = d.get("mc_remaining_time")
    nozzle = fb._to_float(d.get("nozzle_temper"))
    nozzle2 = fb._right_nozzle_temp(d)
    bed = fb._to_float(d.get("bed_temper"))
    chamber_f = fb._chamber_temp(d)
    layer = d.get("layer_num")
    total_layer = d.get("total_layer_num")
    name = d.get("subtask_name") or d.get("gcode_file") or ""
    trays = fb.get_trays(d)

    kids: List[dict] = []

    # Header
    kids.append(_text(4, 2, f"{fb.PRINTER_LABEL}  {stage}", width=150))
    kids.append(_text_right(2, 2, f"{pct}%  {datetime.now().strftime('%H:%M')}"))
    kids.append(_hline(0, HEADER_H - 1, W))

    # Camera frame (the only <img>) or a placeholder box
    if cam_img is not None:
        cam = fb.cover_resize(cam_img.convert("L"), CAM_W, CAM_H)
        kids.append(_el("img", _abs(0, HEADER_H, CAM_W, CAM_H, {"objectFit": "cover"}),
                        src=_png_data_uri(cam), tw="img-dither-diffusion"))
    else:
        kids.append(_el("div", _abs(0, HEADER_H, CAM_W, CAM_H,
                        {"border": "1px solid #000", "boxSizing": "border-box"})))

    rx = RIGHT_X
    ry = HEADER_H + 1
    col_w = W - 4 - rx  # right-column usable width (88px); clamp text to it

    # Temps. No spaces between temps — the ° glyph already separates them, and
    # spaces read as too-wide gaps in the pixel font. Chamber temp moves down
    # onto the AMS-temp row to keep the nozzle/bed line short.
    h_level, h_pct, t_str = fb.get_ams_unit_info(d)
    cs = f" C{chamber_f:.0f}°" if chamber_f is not None else ""
    if nozzle2 is not None:
        # Dual nozzle still needs two temp rows; chamber stays on the bed row.
        kids.append(_text(rx, ry, f"N1{nozzle:.0f}°N2{nozzle2:.0f}°",
                          width=col_w)); ry += 11
        kids.append(_text(rx, ry, f"B{bed:.0f}°{cs}", width=col_w)); ry += 11
        cs = ""  # already shown above; don't repeat on the AMS row
        val_x = rx  # dual-nozzle rows aren't column-aligned
    else:
        # Two columns: nozzle on the left, bed temp aligned at val_x. The AMS
        # temp's chamber value and the humidity % line up under the bed temp.
        val_x = rx + 52
        kids.append(_text(rx, ry, f"N{nozzle:.0f}°", width=val_x - rx))
        kids.append(_text(val_x, ry, f"B{bed:.0f}°", width=W - 4 - val_x)); ry += 11

    # AMS temp (left) + chamber temp aligned at val_x
    if t_str:
        kids.append(_text(rx, ry, f"AMS {fb._to_float(t_str):.0f}°", width=val_x - rx))
        if cs:
            kids.append(_text(val_x, ry, cs.strip(), width=W - 4 - val_x))
        ry += 11
    elif cs:
        kids.append(_text(val_x, ry, cs.strip(), width=W - 4 - val_x)); ry += 11

    # Humidity drops (left) + % aligned at val_x
    if h_level or h_pct is not None:
        if h_level:
            drop_els, _ = _drops(rx, ry + 2, h_level)
            kids.extend(drop_els)
        if h_pct is not None:
            kids.append(_text(val_x, ry, f"{h_pct}%", width=W - 4 - val_x))
        ry += 12

    ry += 2
    kids.append(_hline(rx, ry, W - 4 - rx)); ry += 4

    if trays:
        # remain% is right-anchored; the label gets the space between swatch
        # and percent and is hard-truncated (no ellipsis) when it doesn't fit.
        PCT_RIGHT = 1            # remain% anchored 1px from the screen's right
        PCT_W = 25               # just enough for "100%"; keep the rest for the
                                 # label so "PETG" etc. aren't clipped
        SW = 9                   # swatch size (the dithered img incl. border)
        label_x = rx - 1 + SW + 2  # tight 2px gap after the swatch
        pct_x = W - PCT_RIGHT - PCT_W
        label_w = pct_x - 2 - label_x
        for tr in trays[:4]:
            # swatch rendered as a dithered 1-bit image (same look as the
            # Image-API path), bordered. Nudged down 1px so the 9px swatch sits
            # vertically centered in the 11px text row.
            kids.append(_el("img", _abs(rx - 1, ry + 1, SW, SW,
                            {"border": "1px solid #000", "boxSizing": "border-box"}),
                            src=_swatch_img(tr["color"], SW), tw="img-dither-none"))
            mark = "*" if tr["active"] else " "
            ttype = tr["type"] if not tr["empty"] else "—"
            has_pct = tr["remain"] >= 0 and not tr["empty"]
            # When there's no percent, let the label use the full width.
            lw = label_w if has_pct else (W - 4 - label_x)
            kids.append(_text(label_x, ry, f"{tr['label']}{mark} {ttype[:5]}",
                              width=lw))
            if has_pct:
                kids.append(_text_right(PCT_RIGHT, ry, f"{tr['remain']}%"))
            ry += 11
    else:
        kids.append(_text(rx, ry, "Ext spool")); ry += 11

    ry += 1
    kids.append(_hline(rx, ry, W - 4 - rx)); ry += 2
    if eta:
        kids.append(_text(rx, ry, f"ETA {fb.fmt_eta(eta)}")); ry += 11
    if layer and total_layer:
        kids.append(_text(rx, ry, f"L{layer}/{total_layer}"))

    # Bottom strip
    by = H - BOTTOM_H
    kids.append(_hline(0, by, W))
    short = name if len(name) <= 32 else name[:30] + ".."
    kids.append(_text(4, by + 3, short, width=288))
    kids.append(_bar(4, by + 16, 256, 6, pct))
    kids.append(_text(266, by + 12, f"{pct}%", width=30))

    root = _el("div", {"position": "relative", "width": f"{W}px",
                       "height": f"{H}px", "backgroundColor": WHITE}, children=kids)
    return {"default": [root]}


def build_window_data_only(d: dict, fb) -> dict:
    """Full-width vector layout used when the camera is disabled or fails."""
    stage = d.get("gcode_state") or "?"
    pct = d.get("mc_percent") or 0
    eta = d.get("mc_remaining_time")
    nozzle = fb._to_float(d.get("nozzle_temper"))
    nozzle2 = fb._right_nozzle_temp(d)
    bed = fb._to_float(d.get("bed_temper"))
    chamber_f = fb._chamber_temp(d)
    layer = d.get("layer_num")
    total_layer = d.get("total_layer_num")
    name = d.get("subtask_name") or d.get("gcode_file") or ""
    spd = d.get("spd_lvl")
    tray = fb.tray_label(d)
    trays = fb.get_trays(d)

    kids: List[dict] = []
    y = 2
    kids.append(_text(6, y, f"{fb.PRINTER_LABEL}  {stage}", width=210))
    kids.append(_text_right(8, y + 1, datetime.now().strftime("%H:%M")))
    y += 18
    if name:
        short = name if len(name) < 38 else name[:35] + "..."
        kids.append(_text(6, y, short, width=W - 12))
    y += 14
    kids.append(_text(6, y, f"Progress  {pct}%", width=165))
    if layer and total_layer:
        kids.append(_text(180, y, f"L {layer}/{total_layer}", width=110))
    y += 14
    kids.append(_bar(6, y, 284, 8, pct))
    y += 14

    if nozzle2 is not None:
        kids.append(_text(6, y, f"N1 {nozzle:.0f}°", width=68))
        kids.append(_text(78, y, f"N2 {nozzle2:.0f}°", width=68))
        kids.append(_text(148, y, f"B {bed:.0f}°", width=68))
    else:
        kids.append(_text(6, y, f"N {nozzle:.0f}°", width=68))
        kids.append(_text(78, y, f"B {bed:.0f}°", width=68))
        if chamber_f is not None:
            kids.append(_text(148, y, f"C {chamber_f:.0f}°", width=68))
    extras = []
    if tray:
        extras.append(tray)
    if spd in fb.SPEED_LABEL:
        extras.append(fb.SPEED_LABEL[spd])
    if extras:
        kids.append(_text(220, y, "  ".join(extras), width=70))
    y += 14
    kids.append(_text(6, y, f"ETA  {fb.fmt_eta(eta)}", width=170))
    y += 14
    x = 6
    for tr in trays[:4]:
        label = f"{tr['label']}{'*' if tr['active'] else ''}"
        ttype = tr["type"] if not tr["empty"] else "—"
        kids.append(_text(x, y, f"{label} {ttype[:5]}", width=68))
        x += 72
    kids.append(_text_right(8, H - 13, datetime.now().strftime("%m-%d %H:%M")))

    root = _el("div", {"position": "relative", "width": f"{W}px",
                       "height": f"{H}px", "backgroundColor": WHITE}, children=kids)
    return {"default": [root]}


def build_window_hms(d: dict, fb) -> dict:
    """Rebuild _render_hms (full-screen ALERT) as a Canvas tree, with larger
    pixel fonts: ecode + description use text-pixel-16 so the error is legible
    from a distance. Header bar grows to fit the bigger title."""
    F16 = "text-pixel-16"
    HDR_H = 22
    # Bigger font ≈ ~8px/char; wrap to fewer chars/line and cap rows so the
    # taller text doesn't overflow the 152px screen.
    WRAP_CHARS = (W - 14) // 8

    kids: List[dict] = []
    kids.append(_el("div", _abs(0, 0, W, HDR_H, {"backgroundColor": BLACK})))
    kids.append(_text(4, 3, f"{fb.PRINTER_LABEL} ALERT", width=180, color=WHITE,
                      font=F16, height=16, line_h=16))
    kids.append(_text(W - 86, 5, datetime.now().strftime("%m-%d %H:%M"),
                      width=82, color=WHITE, align="right",
                      font=PIXEL_FONT, height=11, line_h=11))

    y = HDR_H + 4
    for h in (d.get("hms") or []):
        if y > H - 18:
            break
        ecode, desc = fb.hms_describe(h)
        kids.append(_text(4, y, ecode, width=W - 8,
                          font=F16, height=16, line_h=16)); y += 18
        if desc:
            for line in _wrap_chars(desc, WRAP_CHARS)[:2]:
                if y > H - 18:
                    break
                kids.append(_text(8, y, line, width=W - 12,
                                  font=F16, height=16, line_h=16)); y += 17
        y += 3

    stage = d.get("gcode_state") or ""
    kids.append(_text(4, H - 18, f"State: {stage}", width=W - 8,
                      font=F16, height=16, line_h=16))

    root = _el("div", {"position": "relative", "width": f"{W}px", "height": f"{H}px",
                       "backgroundColor": WHITE,
                       "border": "1px solid #000", "boxSizing": "border-box"},
               children=kids)
    return {"default": [root]}


def _wrap_chars(text: str, max_chars: int) -> List[str]:
    """Greedy word-wrap by character count (font-metric-free, for the larger
    HMS pixel font where the device measures more reliably than we can)."""
    out, cur = [], ""
    for w in text.split():
        cand = (cur + " " + w).strip()
        if len(cand) <= max_chars:
            cur = cand
        else:
            if cur:
                out.append(cur)
            cur = w
    if cur:
        out.append(cur)
    return out


# ---------- push ----------

def build_window_status(title: str, lines: List[str]) -> dict:
    """Offline / waiting placeholder (mirrors render_status_image)."""
    kids: List[dict] = [_text(8, 16, title, width=W - 16)]
    y = 44
    for line in lines:
        kids.append(_text(8, y, line, width=W - 16)); y += 16
    kids.append(_text(W - 80, H - 14, datetime.now().strftime("%m-%d %H:%M"),
                      width=76, align="right"))
    root = _el("div", {"position": "relative", "width": f"{W}px", "height": f"{H}px",
                       "backgroundColor": WHITE}, children=kids)
    return {"default": [root]}


def push_window(window: dict, device_id: str, api_key: str, *,
                border: int = 0, refresh_now: bool = True,
                task_alias: Optional[str] = None, timeout: int = 30) -> None:
    body = {"refreshNow": refresh_now,
            "layoutFull": {"tw": "p-0", "style": {"padding": 0}},
            "windowData": window, "border": border}
    if task_alias is not None:
        body["taskAlias"] = task_alias
    r = requests.post(
        f"{QUOTE0_BASE}/{device_id}/canvas", json=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=timeout)
    if not r.ok:
        log.error("Quote/0 Canvas HTTP %s: %s", r.status_code, r.text[:300])
    r.raise_for_status()
    log.info("Quote/0 Canvas: %s", r.json())


def push_canvas_image(image_b64: str, device_id: str, api_key: str, **kw) -> None:
    """Full-screen-PNG fallback (whole rendered image in one <img>)."""
    push_window(build_window_full_image(image_b64), device_id, api_key, **kw)
