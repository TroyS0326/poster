# ComfyUI Reel Video Workflow

1. Build and test a video workflow in ComfyUI GUI (HunyuanVideo 1.5 first on 24 GB VRAM, Wan 2.2 5B second, Wan 2.2 14B FP8 later if stable).
2. Export API workflow JSON.
3. Save as `workflows/reels_video_workflow.json` (local, not committed).
4. Set node IDs in `.env`: positive prompt node required, negative/seed optional.

Do not commit model files or generated outputs.
