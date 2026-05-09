# Reels Bot (separate module)

This repo now includes a separate Reels generator module that does not change existing poster bot behavior.

## Install requirements

```bash
pip install -r requirements.txt
```

Video rendering requires ffmpeg available on PATH because moviepy uses it under the hood. If moviepy/ffmpeg is missing, the command exits with a clear error message.

## Example config

Use `reels_config_example.json` as a starting point:
- `size` defaults to vertical `[1080, 1920]`
- `background.type` supports only `solid`, `gradient`, or `image` (video backgrounds are not supported yet)
- `scenes` defines timed caption lines
- `voiceover` is optional; if not configured or file missing, video still renders silently

## Run the generator

```bash
python -m reels.generate --input reels_config_example.json --output outputs/reel_example.mp4
```

## Notes

- Generated files in `outputs/` are gitignored and should not be committed.
- Missing input file, invalid JSON, invalid colors, invalid scene/background values, and missing rendering dependencies are handled with clear error messages and non-zero exit codes.
- If scene durations are shorter than `duration_seconds`, the final scene is held until the configured end time.

## Future optional extensions

- AI caption/script generation
- AI background image generation
- TTS voiceover providers (env/config-driven)
- reusable templates and brand packs
- scheduler/uploader integration for social platforms


## Storyboard/script generator (JSON only)

Generate a ReelConfig-compatible storyboard JSON from a simple topic:

```bash
python -m reels.storyboard --topic "Why most traders need rules, not motivation" --output outputs/storyboard.json
```

Then render with the existing command:

```bash
python -m reels.generate --input outputs/storyboard.json --output outputs/reel.mp4
```

Useful options:
- `--audience` (optional; brand pack default is used when omitted)
- `--tone` (default: `direct`)
- `--duration-seconds` (default: `18`)
- `--scene-count` (default: `4`)
- `--background-type` (`solid` or `gradient`)
- `--template` (`discipline`, `mistake`, `checklist`, `myth`, `before-after`; default `discipline`)
- `--brand` (`generic`, `xeanvi`; default `generic`)
- `--visual-style` (`fintech_dark`, `workstation`, `abstract_risk`, `market_grid`, `minimal_gradient`; default uses brand pack)
- `--generate-background` generates a local PNG background and writes storyboard JSON with `background.type=image`
- `--background-output` optional `.png` path for generated background (default: `outputs/backgrounds/<safe_name>.png`); requires `--generate-background`
- `--voiceover-script` adds a generated, compliance-checked narration script under `voiceover.script`
- `--voiceover-audio` sets local audio metadata (`.mp3`, `.wav`, `.m4a`, `.aac`) and enables voiceover using provider `local_audio`

Template structures stay concise for vertical overlays and adapt to scene count.

Brand packs provide default audience, default CTA, and color palette settings per brand.

Storyboard generation applies lightweight compliance checks to topic, CTA, and generated scene text. Unsafe phrases are rejected (for example: `guaranteed profits`, `passive income`, `risk-free`, `100% accurate`, `buy now`, `sell now`).

Example with brand + template:

```bash
python -m reels.storyboard --brand xeanvi --template mistake --topic "The cost of breaking your own trading rules" --output outputs/xeanvi_mistake.json
python -m reels.generate --input outputs/xeanvi_mistake.json --output outputs/xeanvi_mistake.mp4
```

AI mode is optional and future-safe. If no AI provider/key is configured, local template mode is used automatically and does not require paid APIs.


Storyboard JSON now includes an optional top-level `visual` field:

```json
"visual": {
  "style": "market_grid",
  "image_prompt": "...",
  "negative_prompt": "...",
  "background_role": "optional_ai_or_manual_background"
}
```

### Local background PNG generator (no external API)

Generate a style-aligned 1080x1920 PNG using Pillow/numpy:

```bash
python -m reels.backgrounds --style fintech_dark --brand xeanvi --output outputs/backgrounds/fintech_dark.png
```

This is separate from storyboard generation.

### Workflows

A. Visual prompt workflow (JSON-only):
1. Run `reels.storyboard` with optional `--visual-style`.
2. Use `visual.image_prompt` + `visual.negative_prompt` later with your AI/manual art workflow.

B. Local PNG workflow:
1. One-command JSON + PNG generation:

```bash
python -m reels.storyboard --brand xeanvi --template mistake --visual-style market_grid --generate-background --background-output outputs/backgrounds/xeanvi_market_grid.png --topic "The cost of breaking your own trading rules" --output outputs/xeanvi_market_grid.json
```

2. Render step remains:

```bash
python -m reels.generate --input outputs/xeanvi_market_grid.json --output outputs/xeanvi_market_grid.mp4
```


### Placeholder voiceover audio generator (no external API)

Generate a silent placeholder WAV that matches storyboard `duration_seconds`:

```bash
python -m reels.voiceover --input outputs/xeanvi_market_grid_voice.json --output outputs/audio/xeanvi_market_grid.wav
```

This creates **silent placeholder audio only** for pipeline validation. It is **not real TTS narration**.

### Voiceover workflow

1. Generate storyboard JSON + PNG background:
```bash
python -m reels.storyboard --brand xeanvi --template mistake --visual-style market_grid --generate-background --background-output outputs/backgrounds/xeanvi_market_grid.png --voiceover-script --voiceover-audio outputs/audio/xeanvi_market_grid.wav --topic "The cost of breaking your own trading rules" --output outputs/xeanvi_market_grid_voice.json
```
2. Generate silent WAV placeholder:
```bash
python -m reels.voiceover --input outputs/xeanvi_market_grid_voice.json --output outputs/audio/xeanvi_market_grid.wav
```
3. (Optional) You can also set `voiceover.audio_path` manually in JSON if you already have local audio.
4. Render MP4:
```bash
python -m reels.generate --input outputs/xeanvi_market_grid_voice.json --output outputs/xeanvi_market_grid_voice.mp4
```

## Batch workflow (local-only, no upload/no paid APIs)

Use a batch JSON file to generate multiple local Reel assets in one run:

```bash
python -m reels.batch --input examples/reels_batch_example.json --output-dir outputs/batch
```

Batch format (`examples/reels_batch_example.json`) supports top-level defaults and per-item overrides:
- Defaults: `brand`, `template`, `visual_style`, `duration_seconds`, `scene_count`, `generate_background`, `generate_voiceover_placeholder`, `render_mp4`
- Each `items[]` entry must include `topic`; optional `slug`; and may override any default field above.
- Boolean fields must be real JSON booleans (`true` / `false`), not strings like `"false"`.

Per-item output paths are predictable:
- `outputs/batch/<slug>/<slug>.json`
- `outputs/batch/<slug>/<slug>.png` (if `generate_background=true`)
- `outputs/batch/<slug>/<slug>.wav` (if `generate_voiceover_placeholder=true`)
- `outputs/batch/<slug>/<slug>.mp4` (if `render_mp4=true` and render succeeds)

Batch writes a machine-readable summary file at:
- `outputs/batch/summary.json`
- `summary.json` now includes run-level metadata: `output_dir`, `total_items`, `success_count`, `failed_count`, `render_failed_count`, and per-item `items[]`.

Batch also writes local operational logs for debugging:
- `outputs/batch/run_report.md` (human-readable run report with counts + per-item table)
- `outputs/batch/events.jsonl` (JSONL event stream with `batch_started`, `item_started`, `storyboard_written`, `background_written`, `voiceover_written`, `render_written`, `item_failed`, `item_completed`, `batch_completed`)

Runtime behavior:
- If `render_mp4=false`, MP4 rendering is skipped.
- If `render_mp4=true` and moviepy/ffmpeg is unavailable, that item is marked failed/render_failed and batch processing continues.
- Compliance guardrails are applied per item topic; failed items do not stop remaining items.

Generated files remain under `outputs/` and are gitignored.
