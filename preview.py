#!/usr/bin/env python3
"""Render mock data with fetch_bambu.render_image and save preview PNGs."""
import base64, io, os, sys
from PIL import Image

os.environ.setdefault("PRINTER_IP", "192.168.1.50")
os.environ.setdefault("PRINTER_SN", "FAKESN0001")
os.environ.setdefault("PRINTER_ACCESS", "00000000")
os.environ.setdefault("QUOTE0_API_KEY", "x")
os.environ.setdefault("QUOTE0_DEVICE_ID", "x")

sys.path.insert(0, os.path.dirname(__file__))
import fetch_bambu as fb

_AMS_FULL = {
    "tray_now": "1",  # ams 0 tray 1 -> T2 active
    "ams": [{
        "id": "0",
        "humidity": "4",
        "temp": "22.7",
        "tray": [
            {"id": "0", "tray_type": "PLA",   "tray_color": "FFFFFFFF", "remain": 80},
            {"id": "1", "tray_type": "PETG",  "tray_color": "000000FF", "remain": 65},
            {"id": "2", "tray_type": "PLA-S", "tray_color": "F95959FF", "remain": 30},
            {"id": "3", "tray_type": ""},
        ],
    }],
}

MOCK_PRINTING = {
    "gcode_state": "RUNNING",
    "mc_percent": 47,
    "mc_remaining_time": 138,
    "nozzle_temper": 215.4,
    "bed_temper": 60.1,
    "chamber_temper": 32.0,
    "layer_num": 142,
    "total_layer_num": 305,
    "subtask_name": "benchy_PLA_0.20mm.gcode",
    "spd_lvl": 2,
    "ams": _AMS_FULL,
    "hms": [],
}

MOCK_IDLE = {
    "gcode_state": "IDLE",
    "mc_percent": 0,
    "mc_remaining_time": 0,
    "nozzle_temper": 24.6,
    "bed_temper": 23.8,
    "chamber_temper": 24.1,
    "subtask_name": "",
    "spd_lvl": 2,
    "ams": _AMS_FULL,
    "hms": [],
}

MOCK_HMS = {
    "gcode_state": "PAUSE",
    "mc_percent": 23,
    "nozzle_temper": 210.0,
    "bed_temper": 60.0,
    "hms": [
        {"attr": 0x07042200, "code": 0x00020025},
    ],
}


def save(name: str, data: dict, scale: int = 3):
    b64 = fb.render_image(data)
    img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("L")
    out = os.path.join(os.path.dirname(__file__), name)
    img.save(out)
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    big.save(out.replace(".png", f"_x{scale}.png"))
    print(f"wrote {out}  ({img.width}x{img.height})")


def fake_camera_frame():
    """Synthesize a placeholder camera scene (gradient + shapes) for preview."""
    from PIL import Image, ImageDraw
    cam = Image.new("L", (640, 480), 90)
    d = ImageDraw.Draw(cam)
    for i in range(480):
        d.line([(0, i), (640, i)], fill=int(40 + i * 0.25))
    d.rectangle([60, 320, 580, 460], fill=180)
    d.rectangle([60, 320, 580, 460], outline=240, width=3)
    d.ellipse([260, 180, 380, 360], fill=70)
    d.ellipse([280, 200, 360, 340], fill=110)
    d.rectangle([300, 100, 340, 220], fill=200)
    return cam


if __name__ == "__main__":
    fb.HMS_DB["0704220000020025"] = (
        "AMS E slot 3 feed resistance is too high. "
        "Please reduce spool rotation resistance and avoid "
        "over-bent or over-long filament tubes."
    )

    fb.SHOW_CAMERA = False
    save("preview_printing.png", MOCK_PRINTING)
    save("preview_idle.png", MOCK_IDLE)
    save("preview_hms.png", MOCK_HMS)

    fb.SHOW_CAMERA = True
    fb.grab_camera_frame = fake_camera_frame
    save("preview_camera.png", MOCK_PRINTING)
