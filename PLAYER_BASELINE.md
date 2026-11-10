# Approved final video player baseline

The user approved this behavior on 2026-11-10 and requested it for other TCL products. Canonical original implementation: [VoxIN EVO T4 commit 43b16ac](https://github.com/TCL-Air-Conditioner/voxin-evo-t4/commit/43b16ac4582c9f8fd0a969a1ca38f0716b30a613).

## Required behavior

1. Show an inline cover extracted automatically from the original video. Remove the cover before calling `video.play()` synchronously from the user's click.
2. Switch topics within the page. Reuse the prepared video element, update the title/directory/URL, support browser back and forward, and preserve ordinary modified-link clicks.
3. Give active playback priority. Warm one next video after at least eight seconds are buffered, or the remainder is buffered. Pause warming on stalls or hidden pages; respect Save-Data and 2G connections.
4. Store verified complete MP4 responses, never a partial 206 response as a full video. Serve byte ranges from complete cached media. Retain at most four media files and 24 MiB.
5. Give each media file a stable content-hash query version. Preserve unchanged cached media when only page code changes. Scope both the worker and cache names to the individual product.
6. Cache visited pages, the next page, logo and small covers. Fall back to ordinary streaming when storage is unavailable. Retain buffering, retry and direct-MP4 controls.
7. Preserve MP4 bytes, quality, public route paths and the original product design. Cache persistence is best effort; the browser may evict stored data. This does not eliminate slow initial network access or unsupported video codecs.

## One-Way Cassette adaptation

- Product title: `TCL One-Way Cassette`.
- Worker scope: `/tcl-one-way/`; cache prefix: `tcl-one-way-`.
- Twelve topics retain their existing directory order, slugs and MP4 names.
- The existing repository publishes static files directly. The builder supports existing generated HTML, so a repeat build produces identical outputs for identical inputs.
- Run `python3 build_pages.py --in-place` after code/media updates, then commit the generated topic pages, `index.html`, `covers/` and `sw.js` along with source changes. No separate cover upload or paid service is required.
- `python3 build_pages.py EMPTY_OUTPUT_DIRECTORY` produces a separate publishable site for review or a future build pipeline.

## Validation

`node --test tests/*.test.cjs` verifies playback event ordering, navigation, warm-up limits, isolation, offline page reuse, hash checking, ranges, storage failure and bounded media retention.

`python3 -m unittest discover -s tests -p test_site.py` builds real pages, verifies all twelve routes, checks every original video byte and proves deterministic regeneration.

Verify the live deployment after publishing. Check actual decoded frames before claiming playback works; do not present cloud-browser timing as WeChat phone measurements.
