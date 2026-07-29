# Third-Party Notices

Quote Bambu's application source is licensed under the MIT License in
[`LICENSE`](LICENSE). The distributed container also contains third-party
software under its own licenses. The MIT License does not relicense those
components.

This notice records the FFmpeg binary included by the project as of v0.8.0. It
is informational and does not replace the license texts or corresponding-source
obligations that apply when distributing a container image.

## FFmpeg 7.1

Quote Bambu invokes FFmpeg as a separate command-line process to capture one
RTSPS camera frame and reads the resulting PNG from standard output.

The container copies `/ffmpeg` from:

- Image: `docker.io/mwader/static-ffmpeg:7.1`
- Multi-platform digest:
  `sha256:a8090df5f5608daef387e1b2e93b98aaacb4d92153ad904e7d715c725724fca4`
- Linux amd64 manifest:
  `sha256:32dfd1df302753d47fb4a87344b5ba005c9cae8e58b4d842959fc387fd004a01`
- Linux arm64 manifest:
  `sha256:84e4edba9212b950f26fb591365ea4f89baf3d8202310b43bcf0128db9fb0992`

The binary reports FFmpeg 7.1 and was configured with, among other options,
`--enable-static`, `--enable-gpl`, `--enable-version3`, `--enable-libx264`, and
`--enable-libx265`. FFmpeg's license documentation states that a build with
GPL parts and `--enable-version3` is governed by GPL version 3 or later.

- License: GNU General Public License version 3 or later
- Full license text:
  [`LICENSES/GPL-3.0-or-later.txt`](LICENSES/GPL-3.0-or-later.txt)
- FFmpeg license explanation:
  <https://github.com/FFmpeg/FFmpeg/blob/n7.1/LICENSE.md>
- FFmpeg 7.1 corresponding source:
  <https://ffmpeg.org/releases/ffmpeg-7.1.tar.bz2>
- FFmpeg source SHA-256:
  `fd59e6160476095082e94150ada5a6032d7dcc282fe38ce682a00c18e7820528`

The final Quote Bambu image also retains the upstream `/doc` directory and
`/versions.json` at `/usr/share/doc/ffmpeg`. The latter lists the exact versions
or commits of the libraries statically linked into the binary.

## static-ffmpeg build definition

The FFmpeg binary was produced by Mattias Wadman's `wader/static-ffmpeg`
project. Its build scripts are MIT licensed; that MIT license applies to the
build project, not to the resulting GPL-enabled FFmpeg binary.

- Build definition tag:
  <https://github.com/wader/static-ffmpeg/tree/7.1>
- Tag commit:
  `caa9e84d10c0dbb6fad4f9d9fe2170c29b1f8b7d`
- Build-source archive:
  <https://github.com/wader/static-ffmpeg/archive/refs/tags/7.1.tar.gz>
- Upstream build-project license:
  [`LICENSES/static-ffmpeg-MIT.txt`](LICENSES/static-ffmpeg-MIT.txt)

The tagged Dockerfile records download URLs, versions or commits, checksums,
patches, and build commands for FFmpeg and its statically linked third-party
libraries. Recipients of a published Quote Bambu container can use that build
definition and the version manifest retained in the image to locate the
corresponding source.

If any linked source becomes unavailable, please open an issue or use the
private reporting route in [`SECURITY.md`](SECURITY.md). Container distributors
remain responsible for satisfying the licenses of FFmpeg and all statically
linked libraries; relying on this notice alone is not a substitute for a
license review.
