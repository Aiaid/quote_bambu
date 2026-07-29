# Contributing to Quote Bambu

Thanks for helping improve Quote Bambu. Bug reports, compatibility reports,
documentation fixes, and focused pull requests are welcome.

## Before opening an issue

- Search existing issues first.
- Remove printer serial numbers, LAN access codes, Quote/0 API keys, IP
  addresses, camera images, and private print-job names from logs/screenshots.
- For model or firmware compatibility reports, include the printer model,
  firmware version, camera protocol, push mode, host architecture, and relevant
  redacted logs.

Security vulnerabilities should follow [SECURITY.md](SECURITY.md), not a public
issue.

## Development setup

Quote Bambu supports Python 3.10+.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-dev.lock
pytest
python preview.py
python preview_canvas.py
```

The preview scripts are offline layout checks and do not require a printer or
Quote/0 credentials.

## Pull requests

Keep changes focused and explain:

1. what problem is being solved;
2. which printer models/protocols are affected;
3. how the change was tested;
4. whether environment variables, screenshots, or README instructions changed.

Add or update tests for parsing, normalization, rendering, and regression fixes.
Do not commit `.env`, access codes, API keys, device serial numbers, or real
camera frames.
