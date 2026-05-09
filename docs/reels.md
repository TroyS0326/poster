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
- `--background-output` optional `.png` path for generated background (default: `outputs/backgrounds/<safe_name>.png`)

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
