import json
import random
import requests
from prompts import CONTENT_PILLARS, SYSTEM_PROMPT

REQUIRED_PACKAGE_FIELDS = ["pillar", "caption", "image_prompt", "negative_prompt"]


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


def _fallback_package(pillar: str) -> dict:
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


def _is_valid_package(package: dict) -> bool:
    if not isinstance(package, dict):
        return False
    return all(isinstance(package.get(field), str) and package.get(field).strip() for field in REQUIRED_PACKAGE_FIELDS)


def generate_content_package(config, logger):
    pillar = random.choice(CONTENT_PILLARS)
    logger.info("content pillar selected: %s", pillar)
    prompt = f"{SYSTEM_PROMPT}\nTarget pillar: {pillar}"
    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{config.gemini_model}:generateContent"
    headers = {"Content-Type": "application/json", "X-goog-api-key": config.gemini_api_key}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        response = requests.post(gemini_url, headers=headers, json=payload, timeout=45)
        response.raise_for_status()
    except requests.RequestException as exc:
        error_response = getattr(exc, "response", None)
        status = getattr(error_response, "status_code", "unknown")
        error_body = ""
        if error_response is not None:
            try:
                error_body = (error_response.text or "").strip()[:300]
            except Exception:
                error_body = ""
        if error_body:
            logger.warning("gemini request failed (status=%s): %s; using fallback", status, error_body)
        else:
            logger.warning("gemini request failed (status=%s): %s; using fallback", status, exc)
        return _fallback_package(pillar)

    try:
        response_json = response.json()
    except ValueError as exc:
        logger.warning("gemini response json decode failed: %s; using fallback", exc)
        return _fallback_package(pillar)

    try:
        text = response_json["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        logger.warning("gemini response missing content parts: %s; using fallback", exc)
        return _fallback_package(pillar)

    parsed = _extract_json(text)
    if not _is_valid_package(parsed):
        logger.warning("gemini parsed package missing required fields; using fallback")
        return _fallback_package(pillar)

    return parsed
