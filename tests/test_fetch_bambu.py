from types import SimpleNamespace

import camera
import fetch_bambu as fb


def _texts(window):
    values = []

    def walk(value):
        if isinstance(value, dict):
            if value.get("type") == "span":
                child = value.get("props", {}).get("children")
                if isinstance(child, str):
                    values.append(child)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(window)
    return values


def test_deep_merge_preserves_unmodified_nested_values():
    state = {"ams": {"humidity": 3, "tray": [{"id": "0"}]}, "mc_percent": 10}
    fb._deep_merge(state, {"ams": {"humidity": 4}, "mc_percent": 11})
    assert state == {
        "ams": {"humidity": 4, "tray": [{"id": "0"}]},
        "mc_percent": 11,
    }


def test_snapshot_is_recursively_independent():
    original = {"ams": {"tray": [{"remain": 80}]}}
    with fb.state["lock"]:
        fb.state["data"] = original

    snapshot = fb.snapshot_state()
    original["ams"]["tray"][0]["remain"] = 1

    assert snapshot["ams"]["tray"][0]["remain"] == 80


def test_config_validation_reports_all_invalid_values(monkeypatch):
    monkeypatch.setattr(fb, "_missing", ["PRINTER_SN"])
    monkeypatch.setattr(fb, "_INTERVAL_RAW", "0")
    monkeypatch.setattr(fb, "INTERVAL_SECONDS", 0)
    monkeypatch.setattr(fb, "PUSH_MODE", "unknown")
    monkeypatch.setattr(fb, "CAMERA_PROTO", "rtsp")

    errors = fb.validate_config()

    assert any("PRINTER_SN" in error for error in errors)
    assert any("INTERVAL_SECONDS" in error for error in errors)
    assert any("PUSH_MODE" in error for error in errors)
    assert any("CAMERA_PROTO" in error for error in errors)

    monkeypatch.setattr(fb, "_INTERVAL_RAW", "not-a-number")
    monkeypatch.setattr(fb, "INTERVAL_SECONDS", 60)
    errors = fb.validate_config()
    assert any("positive integer" in error for error in errors)


def test_preview_style_validation_can_skip_real_credentials(monkeypatch):
    monkeypatch.setattr(fb, "_missing", ["PRINTER_SN", "QUOTE0_API_KEY"])
    monkeypatch.setattr(fb, "_INTERVAL_RAW", "")
    monkeypatch.setattr(fb, "INTERVAL_SECONDS", 60)
    monkeypatch.setattr(fb, "PUSH_MODE", "canvas")
    monkeypatch.setattr(fb, "CAMERA_PROTO", "auto")

    assert fb.validate_config(require_required=False) == []


def test_canvas_uses_full_width_data_only_layout_without_camera(monkeypatch):
    monkeypatch.setattr(fb, "SHOW_CAMERA", False)
    monkeypatch.setattr(fb, "PRINTER_LABEL", "X1C")
    data = {
        "gcode_state": "RUNNING",
        "mc_percent": 47,
        "mc_remaining_time": 12,
        "nozzle_temper": 215,
        "bed_temper": 60,
        "layer_num": 2,
        "total_layer_num": 10,
        "subtask_name": "test.gcode",
        "hms": [],
    }

    window = fb.render_canvas_window(data)
    text = _texts(window)

    assert any(value.startswith("X1C  RUNNING") for value in text)
    assert "Progress  47%" in text
    assert not any(
        node.get("type") == "img"
        for node in window["default"][0]["props"]["children"]
    )

    monkeypatch.setattr(fb, "SHOW_CAMERA", True)
    monkeypatch.setattr(fb, "grab_camera_frame", lambda: None)
    failed_camera_window = fb.render_canvas_window(data)
    assert "Progress  47%" in _texts(failed_camera_window)
    assert not any(
        node.get("type") == "img"
        for node in failed_camera_window["default"][0]["props"]["children"]
    )


def test_ffmpeg_error_redacts_access_code(monkeypatch, caplog):
    access_code = "12345678"
    stderr = (
        b"Unable to open rtsps://bblp:12345678@192.168.1.50:322/"
        b"streaming/live/1"
    )
    monkeypatch.setattr(
        camera.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1, stdout=b"", stderr=stderr
        ),
    )

    assert camera.grab_rtsps("192.168.1.50", access_code) is None
    assert access_code not in caplog.text
    assert "rtsps://***:***@" in caplog.text
