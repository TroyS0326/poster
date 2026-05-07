import json
import random
import time

import requests
from prompts import CONTENT_PILLARS, POST_ARCHETYPES, SYSTEM_PROMPT, VISUAL_DIRECTIONS

REQUIRED_PACKAGE_FIELDS = ["pillar", "archetype", "caption", "image_concept", "image_prompt", "negative_prompt"]


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("json", "", 1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                return None
    return None


def _fallback_packages() -> list[dict]:
    return [
        {
            "pillar": "Revenge trading after one bad loss",
            "archetype": "hard truth",
            "caption": "One loss can make bad risk decisions feel urgent.\n\nXeanVI keeps setup rules and validation visible before execution so emotion does not rewrite your process mid-session.\n\nPause, confirm the playbook, then decide with structure.\n\nNot financial advice. Trading involves risk.\n\n#XeanVI #TradingPsychology #RiskControls #DayTrading",
            "image_concept": "A restrained, high-end workstation scene focused on process control after volatility.",
            "image_prompt": "Cinematic empty workstation scene, premium fintech editorial style, closed journal beside keyboard and coffee, soft monitor glow with abstract blurred chart shapes, clean desk composition, no humans, no body parts, no readable text, vertical 1080x1350",
            "negative_prompt": "hands, fingers, detached limbs, disconnected body parts, malformed anatomy, faces, readable text, fake handwriting, floating papers, distorted UI, fabricated performance screens, platform branding, currency imagery, hype text",
        },
        {
            "pillar": "The trader who abandons their plan too early",
            "archetype": "lesson learned",
            "caption": "Most plan failures come from pressure, not from bad rules.\n\nYou define structure premarket, then stress tries to edit it live. XeanVI keeps validation and risk controls front and center before each action.\n\nLet the checklist speak louder than impulse.\n\nNot financial advice. Trading involves risk.\n\n#XeanVI #ExecutionDiscipline #TradingProcess #RiskControls",
            "image_concept": "A premium flat-lay showing disciplined preparation and clean execution context.",
            "image_prompt": "Premium editorial flat lay of keyboard, closed notebook, and desk lamp on dark textured desk, abstract monitor glow in background, clean fintech mood, no humans, no anatomy, no readable text, vertical 1080x1350",
            "negative_prompt": "hands, fingers, detached limbs, disconnected body parts, malformed anatomy, faces, readable text, fake handwriting, floating papers, distorted UI, fabricated performance visuals, promotional banners",
        },
    ]


def _fallback_package(pillar: str, archetype: str) -> dict:
    packages = _fallback_packages()
    matches = [p for p in packages if p["pillar"] == pillar or p["archetype"] == archetype]
    pool = matches if matches else packages
    return random.choice(pool)


def _is_valid_package(package: dict) -> bool:
    if not isinstance(package, dict):
        return False
    return all(isinstance(package.get(field), str) and package.get(field).strip() for field in REQUIRED_PACKAGE_FIELDS)


def generate_content_package(config, logger):
    pillar = random.choice(CONTENT_PILLARS)
    archetype = random.choice(POST_ARCHETYPES)
    visual_direction = random.choice(VISUAL_DIRECTIONS)
    uniqueness_seed = f"{int(time.time())}-{random.randint(1000, 9999)}"
    logger.info("content selection pillar=%s archetype=%s visual=%s", pillar, archetype, visual_direction)

    prompt = (
        f"{SYSTEM_PROMPT}\n"
        f"Target pillar: {pillar}\n"
        f"Target archetype: {archetype}\n"
        f"Target visual direction: {visual_direction}\n"
        f"Uniqueness seed: {uniqueness_seed}\n"
    )
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.gemini_model}:generateContent"
    headers = {"Content-Type": "application/json", "X-goog-api-key": config.gemini_api_key}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(gemini_url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("gemini request failed: %s; using fallback", exc)
        return _fallback_package(pillar, archetype)

    try:
        response_json = response.json()
        text = response_json["candidates"][0]["content"]["parts"][0]["text"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        logger.warning("gemini response parsing failed: %s; using fallback", exc)
        return _fallback_package(pillar, archetype)

    parsed = _extract_json(text)
    if not _is_valid_package(parsed):
        logger.warning("gemini parsed package missing required fields; using fallback")
        return _fallback_package(pillar, archetype)

    return parsed
