# XeanVI Social Bot (Linux)

## What it does
Python automation bot that every 4 hours: generates a XeanVI-compliant caption + image prompt, generates an AI image, builds/uses a public image URL, and posts to Facebook Page + Instagram Business (or dry-run).

## Setup
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill values.
4. Optional local image hosting: `python dashboard.py`
5. Run bot: `python main.py`

## Recommended simple setup: hosted image API
Use Replicate to avoid managing Stable Diffusion server installs on Vast.ai.

Set in `.env`:
- `IMAGE_PROVIDER=replicate`
- `REPLICATE_API_TOKEN=...` (copy from your Replicate account API tokens page)
- `REPLICATE_MODEL=black-forest-labs/flux-schnell` (or another compatible Replicate model slug)
- `REPLICATE_OUTPUT_FORMAT=jpg` (recommended for Meta/Instagram compatibility)

With Replicate enabled, local Vast.ai/AUTOMATIC1111 Stable Diffusion WebUI is not required for image generation.
With `IMAGE_PROVIDER=replicate`, Vast.ai `dashboard.py` public image hosting is not required for Meta posting.
The bot uses Replicate's returned output URL for posting and also saves a local copy to `images/generated/`.

## Important config notes
- `.env` is local-only and must never be committed.
- Use `.env.example` as your template.
- `IMG_PUBLIC_URL_BASE` is only required when `IMAGE_PROVIDER=auto1111` (local image generation/hosting).
- For local dashboard serving, example: `IMG_PUBLIC_URL_BASE=http://YOUR_PUBLIC_HOST:8080/images/generated/`
- Meta cannot fetch localhost URLs. The image URL must be publicly reachable by Meta.
- `DRY_RUN=true` is safest for first test.
- `MANUAL_REVIEW_MODE=true` generates content but does not post.

## Dry-run mode
Set `DRY_RUN=true` in `.env`. Bot will generate and log, but will not call Meta Graph posting endpoints.

## Env vars
Required always: `GEMINI_API_KEY`.
`GEMINI_MODEL` defaults to `gemini-1.5-flash` and can be changed if Google changes available model names.
When `IMAGE_PROVIDER=auto1111` (default): `SD_API_URL` and `IMG_PUBLIC_URL_BASE` are required.
When `IMAGE_PROVIDER=replicate`: `REPLICATE_API_TOKEN` and `REPLICATE_MODEL` are required (`IMG_PUBLIC_URL_BASE` is optional).
For Meta/Instagram compatibility, use `REPLICATE_OUTPUT_FORMAT=jpg`. WebP output URLs may be rejected by Meta/Instagram.
Required only when `DRY_RUN=false` and `MANUAL_REVIEW_MODE=false`: `META_ACCESS_TOKEN`, `FB_PAGE_ID`, `IG_BUSINESS_ID`.
Defaults include `POST_INTERVAL_HOURS=4`, `META_GRAPH_VERSION=v20.0`, `MAX_GENERATION_ATTEMPTS=3`.

`upload_image` behavior:
- If `IMG_PUBLIC_URL_BASE` ends with `/images/generated`, the URL becomes `<base>/<filename>`.
- Otherwise the URL becomes `<base>/generated/<filename>`.

## Meta requirements
Use a Facebook Page, linked Instagram Business account, and a long-lived Meta access token with permissions to publish page photos and Instagram content.


## Content Quality System
- Posts are generated from a rotating strategy of content pillars, post archetypes, and visual directions.
- Captions are designed to sound human, emotionally grounded, and relevant to retail day trader psychology.
- Images are intentionally varied and matched to each post theme instead of reusing one visual pattern.
- Manual review mode is recommended while tuning quality and brand voice consistency.

## Compliance note
Posts are marketing/educational only. Not financial advice. Trading involves risk.

## Troubleshooting
- Missing config -> bot exits with explicit missing env names.
- Gemini/API malformed response -> safe fallback package is used.
- SD API failure -> post skipped safely.
- FB success + IG fail -> both statuses logged independently.

## Optional advanced local GPU setup (AUTOMATIC1111)
If you prefer local image generation, keep `IMAGE_PROVIDER=auto1111` and run Stable Diffusion WebUI with an accessible API endpoint in `SD_API_URL`.

## Quick syntax check
Run:
- `python -m py_compile *.py`

## Compliance Keyword Guardrails
- The bot rejects get-rich and income-claim language (for example guaranteed outcomes, easy income, passive income, and win-rate hype).
- The bot avoids broker/platform names unless explicitly reviewed and legally approved.
- The bot avoids crypto, forex, options, futures, NFT, and DeFi language for now.
- XeanVI content should focus on infrastructure, discipline, risk controls, playbook validation, paper testing, execution rules, and emotional process control.

## Automated Image Quality Rules
- Automated posts avoid hands, faces, people, and visible anatomy because fast image models can distort body details and reduce production quality.
- For reliable premium output, prefer product UI mockups, empty desk workstation scenes, abstract risk-control visuals, and clean fintech graphics.
- Premium human/editorial images should be generated manually and reviewed before publishing.

## Reels Generator (separate from poster bot)

A separate module is available for local vertical MP4 reel generation without changing existing poster flow.

- Command: `python -m reels.generate --input reels_config_example.json --output outputs/reel_example.mp4`
- Docs: `docs/reels.md`
- Output videos are generated under `outputs/` and are gitignored.
- Reels generator backgrounds: `background.type` supports `solid`, `gradient`, and `image` only (no video backgrounds yet).
- Reels rendering requires `ffmpeg` on PATH for moviepy.
- Storyboard JSON generator: `python -m reels.storyboard --topic "Why most traders need rules, not motivation" --output outputs/storyboard.json`
- Storyboard generator also supports template + brand packs, for example: `python -m reels.storyboard --brand xeanvi --template mistake --topic "The cost of breaking your own trading rules" --output outputs/xeanvi_mistake.json`
- One-command local PNG+JSON storyboard flow: add `--generate-background` (optionally `--background-output outputs/backgrounds/<name>.png`).

- Reels storyboard supports `--visual-style`, and local style backgrounds can be generated with `python -m reels.backgrounds` into `outputs/`.

- Reels supports optional local voiceover metadata and a silent placeholder WAV generator (`python -m reels.voiceover`) with no paid API requirement.
- Reels also supports batch local asset generation from JSON via `python -m reels.batch --input examples/reels_batch_example.json --output-dir outputs/batch`.
- Batch runs also emit local operational logs at `outputs/batch/summary.json`, `outputs/batch/run_report.md`, and `outputs/batch/events.jsonl`.

- reels.voiceover now supports provider-based TTS (`silent` default, optional `edge_tts_optional`).
- Reels now includes a local queue CLI (`python -m reels.queue`) for dry-run and next-pending batch scheduling only (no social upload).

For Reels Vast.ai deployment and operations, see docs/vast_reels_deploy.md
