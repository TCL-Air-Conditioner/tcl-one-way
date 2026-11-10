# TCL product video pages

This project belongs to 空调github天花机. Read `PLAYER_BASELINE.md` before changing playback, caching or deployment.

- The user approved the final VoxIN EVO T4 player as the baseline for subsequent products.
- Preserve original MP4 bytes/quality, existing QR-code URL paths, product titles, logo and visual style.
- Generate covers from the existing MP4 files; do not ask the user to upload separate preview images.
- Keep each product's Service Worker scope and cache names isolated.
- This repository publishes committed static files from the existing Pages configuration. After editing `player.js`, `sw-template.js` or media, regenerate with `python3 build_pages.py --in-place` and commit generated pages, covers and `sw.js` together.
- Validate with `node --test tests/*.test.cjs`, `python3 -m unittest discover -s tests -p test_site.py`, and `git diff --check`.
- Advancing playback time alone does not prove a visible video frame. Distinguish browser checks from real WeChat device testing.
