# One-Way Cassette Mobile Video Cache Implementation Plan

**Goal:** Apply the user-approved VoxIN EVO T4 final player to all 12 existing One-Way Cassette routes.

**Architecture:** Reuse the approved player and verified-media service worker. Keep this repository's existing branch-based Pages publishing: commit generated HTML, covers and worker together so no hosting configuration change is needed.

**Tech Stack:** Static HTML, browser JavaScript, Service Worker/Cache Storage, Python 3 and FFmpeg for generated covers.

**Spec:** The user explicitly requested the final accepted VoxIN EVO T4 implementation, commit `43b16ac4582c9f8fd0a969a1ca38f0716b30a613`, applied here.

## Global Constraints

- Preserve every original MP4 byte, video URL path, logo and existing product style.
- Keep the cache scoped to `/tcl-one-way/`, separate from other products.
- Retain at most four complete videos and 24 MiB of cached media.
- Prepare one next clip only after active playback has sufficient buffer; cancel on stalls or hidden pages, respect Save-Data/2G.
- Remove the cover before synchronous gesture-triggered playback; retain retry and direct-MP4 recovery.
- Generate inline initial covers and versioned small covers without asking the user to upload images.

## Review Focus

1. In-page navigation must preserve the One-Way product title and existing link paths.
2. Cached range responses must use the correct complete source bytes.
3. Quota/storage failures must fall back to native streaming.
4. Rebuilding already-generated HTML must be deterministic.
5. Generated image assets must be included in branch-based Pages publishing.

## Tasks

- [ ] Port the approved cache/player behavior tests, verify they fail before the implementation is present, then port the player and worker with product-specific names.
- [ ] Add a cover/site builder that supports this repository's existing HTML and deterministic regeneration. Test real build output, source-byte preservation and rebuild stability.
- [ ] Document the approved baseline for future products, review the complete change, run the complete checks, and publish the generated static files in one commit.
- [ ] Verify GitHub Pages deployment, all 12 topic pages, cache worker and browser theme navigation. Do not claim WeChat device measurements.
