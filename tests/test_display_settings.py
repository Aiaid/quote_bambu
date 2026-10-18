"""Regression coverage for configurable printer alerts and header timestamps."""

import base64
from datetime import datetime
import io
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image
import pytest

import fetch_bambu as fb


HMS_IGNORED = {"attr": 1, "code": 2}
HMS_VISIBLE = {"attr": 3, "code": 4}
IGNORED_ECODE = "0000000100000002"
VISIBLE_ECODE = "0000000300000004"


class FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 10, 18, 9, 7, tzinfo=tz)


def _spans(value):
    if isinstance(value, dict):
        if value.get("type") == "span":
            yield value["props"]
        for child in value.values():
            yield from _spans(child)
    elif isinstance(value, list):
        for child in value:
            yield from _spans(child)


@pytest.fixture
def display(monkeypatch):
    """Keep tests independent of printer settings and preview import effects."""
    monkeypatch.setattr(fb, "SHOW_HMS", False)
    monkeypatch.setattr(fb, "SHOW_DATE", True)
    monkeypatch.setattr(fb, "SHOW_CAMERA", False)
    monkeypatch.setattr(fb, "PRINTER_LABEL", "P2S")
    monkeypatch.setattr(fb, "HMS_IGNORE", set())
    monkeypatch.setattr(fb, "_last_suppressed", set())
    monkeypatch.setattr(fb, "HMS_DB", {})
    monkeypatch.setattr(fb, "datetime", FixedDatetime)
    monkeypatch.setattr(fb, "grab_camera_frame", lambda: Image.new("RGB", (320, 180), "white"))
    return {
        "gcode_state": "RUNNING",
        "mc_percent": 47,
        "mc_remaining_time": 12,
        "nozzle_temper": 215,
        "bed_temper": 60,
        "layer_num": 2,
        "total_layer_num": 10,
        "subtask_name": "test.gcode",
        "hms": [HMS_IGNORED.copy(), HMS_VISIBLE.copy()],
    }


def _render_text(mode, data, monkeypatch):
    if mode == "canvas":
        spans = list(_spans(fb.render_canvas_window(data)))
        return [str(span["children"]) for span in spans], [
            str(span["children"]) for span in spans
            if float(span["style"]["top"].removesuffix("px")) <= 6
        ]

    drawn = []
    original_text = fb.ImageDraw.ImageDraw.text

    def record_text(draw, xy, text, *args, **kwargs):
        drawn.append((xy, str(text)))
        return original_text(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(fb.ImageDraw.ImageDraw, "text", record_text)
    image = Image.open(io.BytesIO(base64.b64decode(fb.render_image(data))))
    assert image.size == (296, 152)
    assert image.mode == "1"
    return [text for _, text in drawn], [text for (_, y), text in drawn if y <= 6]


@pytest.mark.parametrize(
    ("settings", "expected"),
    [({}, [False, True]), ({"SHOW_HMS": "true", "SHOW_DATE": "false"}, [True, False])],
)
def test_display_config_defaults_and_explicit_overrides(settings, expected):
    env = os.environ.copy()
    for key in ("SHOW_HMS", "SHOW_DATE"):
        env.pop(key, None)
    env.update(settings)
    result = subprocess.run(
        [sys.executable, "-c", "import json, fetch_bambu as fb; print(json.dumps([fb.SHOW_HMS, fb.SHOW_DATE]))"],
        cwd=Path(__file__).resolve().parents[1], env=env,
        capture_output=True, text=True, check=True,
    )
    assert json.loads(result.stdout) == expected


@pytest.mark.parametrize("mode", ["image", "canvas"])
@pytest.mark.parametrize("camera", [False, True])
def test_disabled_hms_preserves_normal_print_view(mode, camera, display, monkeypatch):
    monkeypatch.setattr(fb, "SHOW_CAMERA", camera)
    # Disabled alerts must not even parse malformed entries from the printer.
    display["hms"].append({"attr": "invalid", "code": None})
    text, header = _render_text(mode, display, monkeypatch)
    assert any("P2S  RUNNING" in value for value in header)
    assert not any("ALERT" in value for value in text)
    assert not any(VISIBLE_ECODE in value for value in text)
    assert "47%" in text if camera else "Progress  47%" in text


@pytest.mark.parametrize("mode", ["image", "canvas"])
def test_enabled_hms_filters_ignored_entries(mode, display, monkeypatch):
    monkeypatch.setattr(fb, "SHOW_HMS", True)
    monkeypatch.setattr(fb, "HMS_IGNORE", {IGNORED_ECODE})
    text, header = _render_text(mode, display, monkeypatch)
    assert any("ALERT" in value for value in header)
    assert VISIBLE_ECODE in text
    assert IGNORED_ECODE not in text
    assert display["hms"] == [HMS_IGNORED, HMS_VISIBLE]


@pytest.mark.parametrize("mode", ["image", "canvas"])
def test_all_ignored_hms_returns_to_normal_view(mode, display, monkeypatch):
    monkeypatch.setattr(fb, "SHOW_HMS", True)
    monkeypatch.setattr(fb, "HMS_IGNORE", {IGNORED_ECODE, VISIBLE_ECODE})
    text, header = _render_text(mode, display, monkeypatch)
    assert any("P2S  RUNNING" in value for value in header)
    assert "Progress  47%" in text
    assert not any("ALERT" in value for value in text)


@pytest.mark.parametrize("mode", ["image", "canvas"])
@pytest.mark.parametrize("view", ["camera", "data", "hms"])
@pytest.mark.parametrize("show_date", [False, True])
def test_every_display_header_respects_show_date(mode, view, show_date, display, monkeypatch):
    monkeypatch.setattr(fb, "SHOW_DATE", show_date)
    monkeypatch.setattr(fb, "SHOW_CAMERA", view == "camera")
    monkeypatch.setattr(fb, "SHOW_HMS", view == "hms")
    _, header = _render_text(mode, display, monkeypatch)
    expected = "10-18 09:07" if show_date else "09:07"
    assert expected in header
    assert ("09:07" if show_date else "10-18 09:07") not in header
    if view == "camera":
        assert not any("%" in value for value in header)


@pytest.mark.parametrize("mode", ["image", "canvas"])
@pytest.mark.parametrize("view", ["camera", "data", "hms"])
def test_long_printer_title_cannot_overlap_header_clock(mode, view, display, monkeypatch):
    monkeypatch.setattr(fb, "PRINTER_LABEL", "Very long printer label " * 8)
    monkeypatch.setattr(fb, "SHOW_CAMERA", view == "camera")
    monkeypatch.setattr(fb, "SHOW_HMS", view == "hms")
    if mode == "canvas":
        header = [span for span in _spans(fb.render_canvas_window(display))
                  if float(span["style"]["top"].removesuffix("px")) <= 6]
        title, clock = header
        title_style, clock_style = title["style"], clock["style"]
        title_right = float(title_style["left"].removesuffix("px")) + float(
            title_style["width"].removesuffix("px"))
        clock_left = fb.W - float(clock_style["right"].removesuffix("px")) - float(
            clock_style["width"].removesuffix("px"))
        assert title_style["overflow"] == "hidden"
        assert title_style["textOverflow"] == "ellipsis"
        assert title_right < clock_left
        assert clock["children"] == "10-18 09:07"
        return

    header = []
    original_text = fb.ImageDraw.ImageDraw.text

    def record_header(draw, xy, text, *args, **kwargs):
        if xy[1] <= 6:
            width = draw.textlength(text, font=kwargs.get("font"))
            header.append((xy[0], xy[0] + width, text))
        return original_text(draw, xy, text, *args, **kwargs)

    monkeypatch.setattr(fb.ImageDraw.ImageDraw, "text", record_header)
    fb.render_image(display)
    title, clock = header
    assert title[2].endswith("..")
    assert title[1] < clock[0]
    assert clock[2] == "10-18 09:07"
    assert clock[1] <= fb.W - 4
