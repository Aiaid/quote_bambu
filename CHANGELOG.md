# Changelog

Notable changes to Quote Bambu will be documented here. The project intends to
follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and semantic
versioning once tagged releases begin.

## Unreleased

## 0.8.0 - 2026-07-29

### Added

- Configuration validation and configurable printer display label.
- Full-width Canvas data-only layout.
- Offline pytest regression suite and pinned Python dependency lists.
- Contribution, security, and issue/PR guidance.
- English README and Community Co-Creation submission draft.
- MIT project license and FFmpeg GPL/source distribution notices.
- Dependabot configuration for Python, Docker, and GitHub Actions.

### Changed

- MQTT rendering now uses a recursively independent state snapshot.
- Camera error logs redact the printer access code.
- Camera-disabled and camera-failure Canvas views now use a full-width layout.
- Docker builds pin the FFmpeg source image digest and retain its version
  manifest and documentation.
- Documentation now describes compatibility, privacy, TLS, battery, and
  unofficial-project boundaries more precisely.

### Included baseline

- Bambu LAN MQTT status and optional camera snapshots.
- Quote/0 Image and Canvas push modes.
- Multi-model normalization, offline previews, and multi-architecture
  container publishing.
