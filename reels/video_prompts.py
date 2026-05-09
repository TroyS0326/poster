from __future__ import annotations

SAFETY = "no visible embedded text, no logos, no broker platforms, no profit screenshots, no financial advice text, text-safe composition for captions"

TONE_HINTS = {
    "revenge": "cinematic vertical video of a tense trading workstation, red risk glow, fast chart movement, impulsive energy, market stress implied, no faces, no hands",
    "paper": "vertical cinematic video of a calm trading journal beside a simulated dashboard, practice environment, soft blue lighting, methodical and controlled",
    "execution": "vertical fintech video of structured checklist workflow and trading command center, blue/teal light, validation process, calm disciplined atmosphere",
}


def build_scene_video_prompt(topic: str, scene_text: str) -> str:
    hay = f"{topic} {scene_text}".lower()
    tone = TONE_HINTS["execution"]
    if "revenge" in hay or "overtrading" in hay:
        tone = TONE_HINTS["revenge"]
    elif "paper" in hay or "practice" in hay:
        tone = TONE_HINTS["paper"]
    return f"vertical 9:16 short cinematic video, trading/fintech workstation context, scene meaning: {scene_text}, {tone}, dynamic camera motion, atmospheric lighting, subject action implied, {SAFETY}".strip()
