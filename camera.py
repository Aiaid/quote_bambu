"""Bambu printer camera grab. Two protocols depending on model:

- RTSPS port 322  (P2S, X1 series, H2 series)        -> ffmpeg
- TCP JPEG port 6000  (P1P, P1S, A1, A1 mini)        -> raw socket + TLS

Spec: OpenBambuAPI/video.md
"""
import io
import logging
import os
import socket
import ssl
import struct
import subprocess
from typing import Optional

from PIL import Image

log = logging.getLogger(__name__)


def grab_rtsps(printer_ip: str, access_code: str, timeout: int = 20) -> Optional[Image.Image]:
    url = f"rtsps://bblp:{access_code}@{printer_ip}:322/streaming/live/1"
    cmd = [
        "ffmpeg", "-loglevel", "error", "-rtsp_transport", "tcp",
        "-tls_verify", "0",
        "-y", "-i", url,
        "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        log.warning("ffmpeg timeout")
        return None
    except FileNotFoundError:
        log.warning("ffmpeg not installed")
        return None
    if out.returncode != 0 or not out.stdout:
        log.warning("ffmpeg failed: %s", out.stderr.decode(errors="ignore")[:200])
        return None
    try:
        return Image.open(io.BytesIO(out.stdout))
    except Exception:
        log.exception("decode RTSPS frame")
        return None


def _recv_exact(sock, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(min(65536, n - len(buf)))
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)


def grab_jpeg_tcp(printer_ip: str, access_code: str, timeout: float = 8.0) -> Optional[Image.Image]:
    """P1/A1 series. Connect TLS to :6000, send 80-byte auth, read 16-byte
    frame header + JPEG payload."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    user = b"bblp".ljust(32, b"\x00")
    pwd = access_code.encode("ascii", errors="ignore")[:32].ljust(32, b"\x00")
    auth = struct.pack("<IIII", 0x40, 0x3000, 0, 0) + user + pwd
    try:
        with socket.create_connection((printer_ip, 6000), timeout=timeout) as raw:
            with ctx.wrap_socket(raw, server_hostname=printer_ip) as s:
                s.settimeout(timeout)
                s.sendall(auth)
                header = _recv_exact(s, 16)
                if len(header) < 16:
                    log.warning("JPEG TCP: short header (%d)", len(header))
                    return None
                payload_size, _itrack, _flags, _ = struct.unpack("<IIII", header)
                if not (0 < payload_size <= 4 * 1024 * 1024):
                    log.warning("JPEG TCP: bad payload size %d", payload_size)
                    return None
                jpg = _recv_exact(s, payload_size)
                if len(jpg) != payload_size:
                    log.warning("JPEG TCP: short payload %d/%d", len(jpg), payload_size)
                    return None
                if jpg[:2] != b"\xff\xd8" or jpg[-2:] != b"\xff\xd9":
                    log.warning("JPEG TCP: bad SOI/EOI")
                    return None
                return Image.open(io.BytesIO(jpg))
    except (OSError, ssl.SSLError, struct.error) as e:
        log.warning("JPEG TCP failed: %s", e)
        return None


def _port_open(host: str, port: int, timeout: float = 1.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def grab_camera_frame(printer_ip: str, access_code: str,
                      proto: str = "auto") -> Optional[Image.Image]:
    """Dispatch by env hint. `auto` probes port 322 first."""
    proto = (proto or "auto").lower()
    if proto == "rtsps":
        return grab_rtsps(printer_ip, access_code)
    if proto == "jpeg":
        return grab_jpeg_tcp(printer_ip, access_code)
    if _port_open(printer_ip, 322):
        img = grab_rtsps(printer_ip, access_code)
        if img is not None:
            return img
    return grab_jpeg_tcp(printer_ip, access_code)
