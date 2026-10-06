# Validation - 2026-10-06

Windows / Python 3.12 / Node 22 / pnpm 11.19.0. TypeScript checks and production builds passed locally.
All examples use synthetic data. Local tests do not imply successful hosted CI or quality on real customer data.

3 tests passed, including a real FFmpeg render with punctuation in a caption, MP4 download, 540×960 dimensions, audio track and duration. A separate 3-second live render produced a 35,241-byte MP4. Generated source is a colour/geometry clip, not a client asset.

Docker image built and started locally as a non-root user. Static UI and health endpoint returned successfully. The container generated its synthetic MP4 sample successfully.

## Selected interface verification

Final TypeScript/Vite build passed. Browser review at measured 1454 × 818 desktop and 443 px mobile width found no horizontal page overflow. Escape closes project dialogs. `preview.png` is an actual local application screenshot, not a design mockup.
A real browser export produced a 5-second, 540 × 960 MP4. Thumbnails and audio peaks are derived from the supplied 8-second source.

## Linux rendering

The bundled Linux imageio FFmpeg lacked `drawtext` in a real container run. The Docker image and CI now install distro FFmpeg and select it explicitly; native runs prefer an installed FFmpeg. Final Docker smoke test produced and downloaded a real 2-second MP4 with a caption. The 3 backend tests also passed again on Windows.
