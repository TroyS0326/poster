# XeanVI Social Bot (Linux)

## What it does
Python automation bot that every 4 hours: generates a XeanVI-compliant caption + image prompt, generates an AI image via Stable Diffusion API, builds a public image URL, and posts to Facebook Page + Instagram Business (or dry-run).

## Setup
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill values.
4. Optional local image hosting: `python dashboard.py`
5. Run bot: `python main.py`

## Dry-run mode
Set `DRY_RUN=true` in `.env`. Bot will generate and log, but will not call Meta Graph posting endpoints.

## Env vars
Required: `GEMINI_API_KEY`, `SD_API_URL`, `IMG_PUBLIC_URL_BASE`.
Required when `DRY_RUN=false`: `META_ACCESS_TOKEN`, `FB_PAGE_ID`, `IG_BUSINESS_ID`.
Defaults include `POST_INTERVAL_HOURS=4`, `META_GRAPH_VERSION=v20.0`, `MAX_GENERATION_ATTEMPTS=3`.

## Meta requirements
Use a Facebook Page, linked Instagram Business account, and a long-lived Meta access token with permissions to publish page photos and Instagram content.

## Compliance note
Posts are marketing/educational only. Not financial advice. Trading involves risk.

## Troubleshooting
- Missing config -> bot exits with explicit missing env names.
- Gemini JSON malformed -> safe JSON extraction + fallback package.
- SD API failure -> post skipped safely.
- FB success + IG fail -> both statuses logged independently.
