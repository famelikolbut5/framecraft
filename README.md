# Framecraft

Turn a local video into a captioned vertical MP4 with real FFmpeg render progress.

![Interface](docs/preview.png)

[Validation notes](docs/VALIDATION.md) · [Source license](LICENSE)

## What it does

Видео - фрагмент - центральное кадрирование 9:16 - титр - MP4 с аудио. Прогресс приходит из FFmpeg.

Upload - trim - central 9:16 crop - caption - real MP4, with FFmpeg progress and download.

Independent portfolio demo, written from scratch. Synthetic examples only. No commercial source, proprietary prompts, client recordings or customer data.

## Run locally

Python 3.12, Node 22 and pnpm 11.19.0:

On Debian/Ubuntu, install `ffmpeg fonts-dejavu-core` first. Linux rendering needs FFmpeg with the `drawtext` filter; the Docker image includes it. `IMAGEIO_FFMPEG_EXE` can select another compatible executable.

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
pnpm install --frozen-lockfile
pnpm build
uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000. For UI development: `pnpm dev` (API proxy expects port 8000).

```sh
docker compose up --build
```

Local-only binding is deliberate. These demos have no user authentication and are not hardened multi-user hosted services.

## Checks and delivery

```sh
pip install pytest httpx
pytest -q
pnpm build
```

GitHub Actions runs backend checks, TypeScript/build checks and Docker image build. Model credentials are never included in CI or a public image.

## Boundaries

Одна задача за раз. Один титр, без интеллектуального трекинга лица. Процессы и статусы хранятся в памяти; после перезапуска готовый файл остаётся в data, но API-история не восстанавливается.

The full application runs locally with its Python backend. A static build alone cannot transcribe audio, execute workflows, render video or call Codex.

## Stack and attribution

Python / FastAPI / React / TypeScript / Vite / Motion / Lucide. Google Fonts: Golos Text (SIL OFL). All third-party dependencies retain their own licenses. See `THIRD_PARTY.md`.

MIT for independently authored source. Asset provenance and actual validation: `docs/VALIDATION.md`.
