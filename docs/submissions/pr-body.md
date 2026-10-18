## Summary

Adds Quote Bambu to the Quote software directory, with English, Simplified Chinese, and Japanese pages and matching navigation entries.

Quote Bambu displays Bambu Lab printer status and optional camera snapshots on Quote/0 through a self-hosted Docker service.

Includes an original device photo, feature overview, setup links, and compatibility and privacy notes.

## Pages and languages

- `en-US/service/co_create/software/quote_bambu.mdx`
- `zh-Hans-CN/service/co_create/software/quote_bambu.mdx`
- `ja-JP/service/co_create/software/quote_bambu.mdx`
- Add `../quote_bambu` to the corresponding `quote/meta.json` navigation files.

## Sources

- Project: https://github.com/Aiaid/quote_bambu
- English setup: https://github.com/Aiaid/quote_bambu/blob/main/README.en.md
- Chinese setup: https://github.com/Aiaid/quote_bambu/blob/main/README.md
- Security notes: https://github.com/Aiaid/quote_bambu/blob/main/SECURITY.md
- Author-provided device photo: https://raw.githubusercontent.com/Aiaid/quote_bambu/main/docs/media/quote-bambu-live-original.jpg

## Review notes

Checked MDX frontmatter structure, existing shared components, all three navigation JSON files, matching feature descriptions, and the public project/photo links. The photo is a format-converted and resized original capture without AI retouching; its final published file was checked for EXIF, GPS, XMP, and IPTC metadata. Compatibility claims distinguish development targets from physical-device testing.

Checks were performed on source files; the website was not rendered. No test run was performed for these documentation-only changes.

## Checklist

- [x] I followed the surrounding documentation style and reused existing MDX components where applicable.
- [x] I identified the included languages and updated navigation.
- [x] I removed credentials, private links, device identifiers, and personal information from examples and screenshots.
