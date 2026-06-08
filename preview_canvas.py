#!/usr/bin/env python3
"""Offline preview of the Canvas (vector) layout.

Mirrors preview.py but for PUSH_MODE=canvas. It builds the Canvas element tree
with quote0_canvas.build_window_*, then approximates how the device renders it
(absolute-positioned div/span/img, pixel font, dithered swatches) to a PNG so
layout can be checked without a device.

This is an APPROXIMATION: the real device uses its own pixel fonts
(text-pixel-12-zpix / text-pixel-16), so on-device text width and glyphs differ
slightly. Use it for positioning/overlap, not pixel-exact fidelity.

    python3 preview_canvas.py
    open canvas_camera_x3.png
"""
import base64
import io
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

os.environ.setdefault("PRINTER_IP", "192.168.1.50")
os.environ.setdefault("PRINTER_SN", "FAKESN0001")
os.environ.setdefault("PRINTER_ACCESS", "00000000")
os.environ.setdefault("QUOTE0_API_KEY", "x")
os.environ.setdefault("QUOTE0_DEVICE_ID", "x")
os.environ["PUSH_MODE"] = "canvas"

sys.path.insert(0, os.path.dirname(__file__))
import fetch_bambu as fb  # noqa: E402
from preview import MOCK_PRINTING, MOCK_HMS, fake_camera_frame  # noqa: E402

W, H = fb.W, fb.H


def _font(px):
    for p in ("/System/Library/Fonts/Supplemental/Arial.ttf",
              "/Library/Fonts/Arial.ttf",
              "/System/Library/Fonts/Helvetica.ttc"):
        try:
            return ImageFont.truetype(p, px)
        except OSError:
            continue
    return ImageFont.load_default()


def _px(v, default=0):
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return int(v)
    m = re.match(r"(-?\d+(?:\.\d+)?)px", str(v))
    return int(float(m.group(1))) if m else default


def _col(c, default=None):
    if not c:
        return default
    c = str(c)
    if c in ("#000", "#000000", "black"):
        return 0
    if c in ("#fff", "#ffffff", "white"):
        return 255
    return default


def _fsize(tw):
    m = re.search(r"text-pixel-(\d+)", tw or "")
    return int(m.group(1)) if m else 11


def _render(window, name, scale=3):
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)

    def walk(el, ox, oy):
        t = el["type"]
        p = el.get("props", {})
        s = p.get("style", {}) or {}
        has_right = "right" in s
        l = ox + _px(s.get("left"))
        tp = oy + _px(s.get("top"))
        w = _px(s.get("width"), W)
        h = _px(s.get("height"), 11)
        bg = _col(s.get("backgroundColor"))
        if bg is not None and t != "span":
            d.rectangle([l, tp, l + w - 1, tp + h - 1], fill=bg)
        if t == "img" and p.get("src", "").startswith("data:image"):
            b64 = p["src"].split(",", 1)[1]
            im = Image.open(io.BytesIO(base64.b64decode(b64))).convert("L")
            if s.get("border"):  # swatch: leave 1px for the border
                d.rectangle([l, tp, l + w - 1, tp + h - 1], outline=0)
                im = im.resize((max(1, w - 2), max(1, h - 2)), Image.NEAREST)
                img.paste(im, (l + 1, tp + 1))
            else:
                img.paste(im.resize((max(1, w), max(1, h))), (l, tp))
        elif s.get("border"):
            bw = 2 if "2px" in str(s.get("border")) else 1
            for o in range(bw):
                d.rectangle([l + o, tp + o, l + w - 1 - o, tp + h - 1 - o], outline=0)
        ch = p.get("children")
        if t == "span" and isinstance(ch, str):
            fg = _col(s.get("color"), 0)
            f = _font(_fsize(p.get("tw")))
            txt = ch
            if not has_right and s.get("width") and d.textlength(txt, font=f) > w:
                ell = "…" if s.get("textOverflow") == "ellipsis" else ""
                while txt and d.textlength(txt + ell, font=f) > w:
                    txt = txt[:-1]
                txt = txt + ell
            tw = d.textlength(txt, font=f)
            if has_right:
                tx = W - _px(s.get("right")) - tw
            else:
                tx = l + (w - tw) if s.get("textAlign") == "right" else l
            d.text((tx, tp - 1), txt, fill=fg if fg is not None else 0, font=f)
        elif isinstance(ch, list):
            for c in ch:
                walk(c, l if t == "div" else ox, tp if t == "div" else oy)
        elif isinstance(ch, dict):
            walk(ch, l, tp)

    for el in window["default"]:
        walk(el, 0, 0)

    out = os.path.join(os.path.dirname(__file__), name)
    img.convert("1").save(out)
    big = img.convert("1").resize((W * scale, H * scale), Image.NEAREST)
    big.save(out.replace(".png", f"_x{scale}.png"))
    print(f"wrote {out}  ({W}x{H})")


if __name__ == "__main__":
    fb.HMS_DB["0704220000020025"] = (
        "AMS feed resistance too high. Reduce spool rotation resistance "
        "and avoid over-bent or over-long filament tubes."
    )
    fb.grab_camera_frame = fake_camera_frame
    _render(fb.render_canvas_window(MOCK_PRINTING), "canvas_camera.png")

    fb.grab_camera_frame = lambda: None
    _render(fb.render_canvas_window(MOCK_PRINTING), "canvas_dataonly.png")
    _render(fb.render_canvas_window(MOCK_HMS), "canvas_hms.png")
