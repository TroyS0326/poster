from __future__ import annotations
import json
import os
import re
import requests
from reels.compliance import validate_compliance_text

GEMINI_SCRIPT_PROMPT = """You are a professional short-form video scriptwriter for XeanVI — a trading discipline platform built for active retail traders.

Write a punchy 4-scene vertical reel script on this topic: {topic}

TONE: Real trader talking to another trader. Raw, honest, direct, personal.
NOT corporate. NOT generic. NOT a software pitch.
Think: someone who has actually blown up an account sharing what they learned.

SCENE RULES:
Scene 1 - HOOK (3-4 seconds): Gut-punch opening. Max 8 words. Make them stop scrolling. Start with "you" or a confession or a hard truth.
Scene 2 - PROBLEM (4-5 seconds): The real pain. What they feel in the moment. Personal, emotional, specific.
Scene 3 - INSIGHT (4-5 seconds): The reframe that changes how they think. Not a product feature. A truth.
Scene 4 - CTA (3-4 seconds): One line about XeanVI + what to do. Authentic. Not salesy.

AVOID: utilize, leverage, synergy, harness, empower, transform, elevate, unlock, journey, game-changer
AVOID: Any profit claims, guaranteed results, financial advice
AVOID: Mentioning broker names, specific strategies, trade signals
KEEP: Under 12 words per scene. Punchy. Conversational. Real.

VOICEOVER: Write the full flowing script connecting all 4 scenes naturally. 
Should sound like one person speaking — not 4 separate sentences stitched together.
Conversational rhythm. Pause points. Like a podcast clip, not a commercial.

Return ONLY valid JSON, no markdown:
{{
  "hook": "scene 1 text",
  "problem": "scene 2 text",
  "insight": "scene 3 text",
  "cta": "scene 4 text",
  "voiceover": "full flowing voiceover script here"
}}"""

def _call_gemini(prompt: str, api_key: str, model: str) -> dict | None:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {"Content-Type": "application/json", "X-goog-api-key": api_key}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=45)
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"```(?:json)?", "", text).strip().strip("`")
        return json.loads(text)
    except Exception:
        return None

def generate_reel_script(topic: str) -> dict | None:
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()
    if not api_key:
        return None
    prompt = GEMINI_SCRIPT_PROMPT.format(topic=topic)
    result = _call_gemini(prompt, api_key, model)
    if not result:
        return None
    required = {"hook", "problem", "insight", "cta", "voiceover"}
    if not required.issubset(result.keys()):
        return None
    for field in required:
        try:
            validate_compliance_text(str(result[field]), field)
        except ValueError:
            return None
    return result
