import json
import random
import requests
from prompts import CONTENT_PILLARS, SYSTEM_PROMPT


GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


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


def generate_content_package(config, logger):
    pillar = random.choice(CONTENT_PILLARS)
    logger.info("content pillar selected: %s", pillar)
    prompt = f"{SYSTEM_PROMPT}\nTarget pillar: {pillar}"
    headers = {"Content-Type": "application/json", "X-goog-api-key": config.gemini_api_key}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(GEMINI_URL, headers=headers, json=payload, timeout=45)
    response.raise_for_status()
    text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
    parsed = _extract_json(text)
    if parsed:
        return parsed

    logger.warning("gemini json parse failed, using safe fallback")
    return {
        "pillar": pillar,
        "caption": (
            "Discipline is a process, not a mood. XeanVI helps retail day traders execute rule-based playbooks "
            "with automated validation and bracket-order risk controls so decisions stay structured under pressure. "
            "Build the playbook before you take the trade. Not financial advice. Trading involves risk. "
            "#XeanVI #TradingDiscipline #DayTrading #RiskManagement"
        ),
        "image_prompt": "Premium dark-mode trading command center UI, AI market scanner panels, disciplined trader workstation, electric blue and charcoal palette, clean SaaS fintech aesthetic, realistic lighting, 1080x1350 vertical composition",
        "negative_prompt": "blurry, deformed text, fake logos, luxury lifestyle, cash piles, fake profit screenshots, childish cartoon style, low quality, distorted UI",
    }
