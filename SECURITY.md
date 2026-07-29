# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 0.8.x | Yes |
| < 0.8 | No |

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting page:

<https://github.com/Aiaid/quote_bambu/security/advisories/new>

Do not include printer access codes, Quote/0 API keys, serial numbers, IP
addresses, camera frames, or private job names in a public issue. If private
reporting is unavailable, open a public issue titled `Security contact request`
without vulnerability details so a maintainer can arrange a private channel.

Please include affected versions, impact, reproduction steps, and any proposed
mitigation. Allow maintainers reasonable time to investigate and publish a fix
before public disclosure.

## Security notes for operators

- The service handles a Bambu LAN access code and a Quote/0 API key.
- Printer MQTT and camera TLS verification is currently disabled for
  compatibility with printer-local certificates.
- The RTSPS access code must currently be passed to ffmpeg in its input URL.
  Quote Bambu redacts ffmpeg diagnostics, but a privileged host user may still
  observe the code in the process argument list while a frame is captured.
- Run the container only on a trusted LAN and never publish printer MQTT,
  RTSPS, or JPEG ports to the internet.
