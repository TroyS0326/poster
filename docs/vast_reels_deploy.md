# Vast.ai Reels Bot Deployment & Operations Guide

This runbook is for running the Reels workflow on a Vast.ai Ubuntu/Linux instance (CUDA 12.4, 24 GB VRAM, 64 GB RAM, AMD EPYC CPU, 32 GB disk, no persistent volume).

## A. What this Reels bot does

The current Reels workflow supports:

- local storyboard generation
- local PNG background generation
- optional silent WAV placeholder
- optional `edge_tts_optional` provider if installed
- batch generation
- queue dry-run / run-id / next
- MP4 rendering
- no social upload yet

## B. Server warning

- Outputs are stored under `outputs/`.
- This Vast.ai instance has no persistent volume.
- Generated files can be lost if the instance is destroyed.
- A 32 GB disk can fill up quickly with MP4 files.
- Back up `outputs/` before destroying or restarting the instance if you need to keep artifacts.

## C. First-time install from GitHub

```bash
cd /workspace
git clone https://github.com/TroyS0326/poster.git
cd poster
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
apt-get update
apt-get install -y ffmpeg
```

Notes:

- If you are not root, use `sudo` for `apt-get` commands.
- `ffmpeg` is required for MP4 rendering.
- `edge-tts` is optional only.

## D. Updating an existing clone

```bash
cd /workspace/poster
git pull origin main
source .venv/bin/activate
pip install -r requirements.txt
```

## E. Environment file

The current Reels flow primarily uses CLI flags and JSON inputs, and does not require many environment variables.

You can still add this optional/future-friendly section to your local `.env.example` (or `.env`) for operator convenience:

```dotenv
# Reels local workflow
REELS_OUTPUT_ROOT=outputs
REELS_DEFAULT_BRAND=xeanvi
REELS_DEFAULT_TEMPLATE=mistake
REELS_DEFAULT_VISUAL_STYLE=market_grid
REELS_TTS_PROVIDER=silent
REELS_EDGE_TTS_VOICE=en-US-AriaNeural
```

Warnings:

- Do not commit `.env`.
- The existing poster bot may still need its own Gemini/Replicate/Meta variables when used separately.

## F. Smoke test commands

```bash
python -m reels.storyboard --topic "Why traders need rules" --output outputs/smoke/storyboard.json

python -m reels.storyboard --brand xeanvi --template mistake --visual-style market_grid --generate-background --background-output outputs/smoke/bg.png --voiceover-script --voiceover-audio outputs/smoke/audio.wav --topic "The cost of breaking your own trading rules" --output outputs/smoke/reel.json

python -m reels.voiceover --input outputs/smoke/reel.json --output outputs/smoke/audio.wav --provider silent

python -m reels.generate --input outputs/smoke/reel.json --output outputs/smoke/reel.mp4
```

## G. Batch test

```bash
python -m reels.batch --input examples/reels_batch_example.json --output-dir outputs/batch
```

Verify outputs:

```bash
ls outputs/batch
cat outputs/batch/summary.json
cat outputs/batch/run_report.md
tail -n 20 outputs/batch/events.jsonl
```

## H. Queue test

```bash
python -m reels.queue --input examples/reels_queue_example.json --list-runs
python -m reels.queue --input examples/reels_queue_example.json --run-id day_01 --dry-run
python -m reels.queue --input examples/reels_queue_example.json --run-id day_01
python -m reels.queue --input examples/reels_queue_example.json --next
```

## I. Optional Edge TTS

Install optional dependency:

```bash
pip install edge-tts
```

Then run:

```bash
python -m reels.voiceover --input outputs/smoke/reel.json --output outputs/smoke/edge.mp3 --provider edge_tts_optional --voice en-US-AriaNeural --format mp3
```

Notes:

- Requires internet access.
- If dependency is missing, the command fails clearly.
- Real TTS requires `voiceover.script` to exist in the input JSON.

## J. Running with tmux/nohup

Example with `tmux`:

```bash
apt-get install -y tmux
tmux new -s reels
cd /workspace/poster
source .venv/bin/activate
python -m reels.queue --input examples/reels_queue_example.json --next
```

Detach:

- `Ctrl+B`, then `D`

Reattach:

```bash
tmux attach -t reels
```

## K. Cron-style usage

Do not implement cron here, but a cron job can call:

```bash
cd /workspace/poster && . .venv/bin/activate && python -m reels.queue --input examples/reels_queue_example.json --next
```

Operational notes:

- Start with `--dry-run` first.
- Check `outputs/queue/<run_id>/summary.json` and `events.jsonl`.

## L. Disk cleanup

```bash
du -h -d 2 outputs | sort -h
find outputs -name "*.mp4" -type f -mtime +7 -delete
find outputs -name "*.wav" -type f -mtime +7 -delete
find outputs -name "*.png" -type f -mtime +14 -delete
```

## M. Backup outputs

```bash
tar -czf reels_outputs_backup.tar.gz outputs/
ls -lh reels_outputs_backup.tar.gz
```

Notes:

- Download or move the backup before destroying the instance.
- No persistent volume means data can be lost.

## N. Troubleshooting

Common issues and checks:

- **`ffmpeg` missing**: install it with `apt-get install -y ffmpeg` (or `sudo apt-get install -y ffmpeg`).
- **`moviepy` missing**: run `pip install -r requirements.txt` inside the active `.venv`.
- **`background.path does not exist`**: verify background file paths and rerun background generation.
- **`edge-tts` missing**: install optional package `pip install edge-tts`, or switch to `--provider silent`.
- **dry-run failing validation**: review the input queue JSON and rerun `--dry-run` until clean.
- **disk full**: prune older `outputs/` artifacts and/or export backups off-instance.
- **no output when using `--next`**: all runs may already be complete; use `--list-runs` to confirm remaining work.
- **generated videos too large**: reduce batch volume, clean old files more aggressively, and back up/remove older MP4s.
