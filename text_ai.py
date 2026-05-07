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
            "caption": "One rough loss can make reckless decisions feel justified.\n\nThe fix is structure before emotion: keep setup criteria, validation checks, and risk limits visible before any next action. That pause protects your process when pressure spikes.\n\nXeanVI is built to keep rules in front of you when discipline gets tested.\n\nNot financial advice. Trading involves risk.\n\n#XeanVI #TradingDiscipline #RiskControls #DayTrading",
            "image_concept": "A tense but clean workstation scene emphasizing discipline returning after a setback.",
            "image_prompt": "Premium product UI mockup on dark background, abstract dashboard cards for setup validation and risk controls, blurred chart shapes, cinematic lighting, clean fintech editorial style, object-only composition, vertical 1080x1350",
            "negative_prompt": "hands, hand, fingers, finger, face, faces, person, people, human, humans, arms, body parts, holding objects, portrait framing, beard, eyes, detached limbs, malformed anatomy, readable text, fake handwriting",
        },
        {
            "pillar": "The trader who abandons their plan too early",
            "archetype": "lesson learned",
            "caption": "Most plan failures are emotional, not technical.\n\nA solid playbook can still collapse when you override it mid-session. Keep validation gates and risk boundaries fixed so stress cannot rewrite your rules in real time.\n\nUse XeanVI to anchor execution to the plan you trusted before the open.\n\nNot financial advice. Trading involves risk.\n\n#XeanVI #ExecutionRules #TradingMindset #RiskControls",
            "image_concept": "A minimal rule-board visual contrasting order and impulse.",
            "image_prompt": "Tactical rule-board style graphic with abstract blocks, clean SaaS dashboard cards for rules and validation, blurred placeholders only, dark neutral palette, high-contrast editorial lighting, interface-only composition, vertical 1080x1350",
            "negative_prompt": "hands, fingers, face, person, people, human, humans, body, arm, holding, over-the-shoulder, portrait, eyes, beard, detached limbs, malformed anatomy, readable text, ticker labels",
        },
        {
            "pillar": "Paper trading as a serious testing lab, not a toy",
            "archetype": "checklist",
            "caption": "Paper testing is where discipline is measured, not where ego is protected.\n\nTrack setup quality, rule adherence, and exit consistency like a lab process. Clean repetitions expose weak assumptions before pressure becomes expensive.\n\nXeanVI helps turn paper sessions into structured evidence for your playbook.\n\nNot financial advice. Trading involves risk.\n\n#XeanVI #PaperTesting #TradingProcess #DayTrading",
            "image_concept": "An analytical flat-lay focused on repeatable testing workflow.",
            "image_prompt": "Close-up flat lay of notebook and keyboard on matte desk, subtle monitor glow, abstract process diagram overlays, premium editorial style, soft directional lighting, object-only composition, vertical 1080x1350",
            "negative_prompt": "hands, fingers, face, person, people, human, humans, body parts, arms, holding paper, portrait, beard, eyes, detached limbs, distorted anatomy, readable text, fake notes",
        },
        {
            "pillar": "Why automation should enforce rules, not replace judgment",
            "archetype": "myth vs reality",
            "caption": "Automation is strongest when it enforces discipline, not when it pretends to think for you.\n\nRules, validation, and risk boundaries should run automatically, while judgment still decides context and restraint. That division keeps your process grounded.\n\nXeanVI is designed to enforce guardrails so your decisions stay deliberate.\n\nNot financial advice. Trading involves risk.\n\n#XeanVI #Automation #RiskManagement #TradingDiscipline",
            "image_concept": "A clean product dashboard visual showing guardrails and controlled decision flow.",
            "image_prompt": "Clean SaaS dashboard cards for rules, validation, and risk, abstract AI scanner interface elements, blurred placeholders only, cinematic monitor glow, dark fintech hero treatment, interface-only composition, vertical 1080x1350",
            "negative_prompt": "hands, fingers, face, faces, person, people, human, humans, body, arm, holding, portrait, over-the-shoulder, eyes, beard, detached limbs, malformed anatomy, readable labels",
        },
        {
            "pillar": "The quiet discipline of walking away from bad setups",
            "archetype": "quiet warning",
            "caption": "Walking away can be the most disciplined action in a session.\n\nWeak setups often tempt action through boredom or urgency. A defined no-trade standard protects focus and keeps your playbook consistent when nothing clean is present.\n\nXeanVI reinforces that restraint by keeping qualification rules impossible to ignore.\n\nNot financial advice. Trading involves risk.\n\n#XeanVI #TraderPsychology #ExecutionDiscipline #RiskControls",
            "image_concept": "A calm empty workstation conveying restraint and controlled patience.",
            "image_prompt": "Empty chair facing soft monitor glow, early-morning workstation with closed journal, keyboard, and coffee, muted cinematic palette, premium editorial composition, silhouette-free workstation scene, vertical 1080x1350",
            "negative_prompt": "hands, fingers, face, person, people, human, humans, body parts, arm, holding, portrait, beard, eyes, detached limbs, malformed anatomy, readable text, fake account screens",
        },
        {
            "pillar": "Bracket orders as emotional guardrails",
            "archetype": "one sharp rule",
            "caption": "Guardrails matter most before pressure arrives.\n\nPredefined risk boundaries reduce impulsive edits during fast conditions and keep exits tied to process instead of panic. Consistency starts with decisions made while calm.\n\nXeanVI keeps bracket-style risk structure visible so execution stays rule-first.\n\nNot financial advice. Trading involves risk.\n\n#XeanVI #RiskControls #ExecutionRules #TradingProcess",
            "image_concept": "An abstract risk-rail graphic centered on pre-committed execution boundaries.",
            "image_prompt": "Abstract risk-control rails around a central decision point, minimal compliance-safe infographic layout with abstract blocks only, crisp geometric depth, dark fintech palette, text-free graphic, vertical 1080x1350",
            "negative_prompt": "hands, fingers, face, person, people, human, humans, body, arm, holding objects, portrait framing, eyes, beard, detached limbs, distorted anatomy, readable text",
        },
        {
            "pillar": "Overtrading from boredom",
            "archetype": "trader mistake breakdown",
            "caption": "Boredom can quietly break discipline faster than volatility.\n\nWhen activity slows, forcing low-quality actions feels productive but usually weakens rule adherence. A clear participation filter protects attention and keeps your process selective.\n\nXeanVI helps enforce patience by requiring criteria before execution can move forward.\n\nNot financial advice. Trading involves risk.\n\n#XeanVI #Overtrading #TradingDiscipline #RiskManagement",
            "image_concept": "A split concept visual showing noisy impulse versus structured restraint.",
            "image_prompt": "Split-screen concept showing chaos versus discipline using abstract shapes only, one side noisy scattered visual noise and the other side clean structured UI blocks, premium fintech editorial lighting, object-only composition, vertical 1080x1350",
            "negative_prompt": "hands, fingers, face, person, people, human, humans, body parts, arm, holding, over-the-shoulder, portrait, beard, eyes, detached limbs, malformed anatomy, readable claims",
        },
        {
            "pillar": "The pain of watching a good setup and hesitating",
            "archetype": "confession",
            "caption": "Hesitation hurts most when your rules were already clear.\n\nSecond-guessing often appears right at execution, after the setup qualifies. Rehearsed checklists and pre-commit steps reduce that freeze and keep decisions aligned with process.\n\nXeanVI supports that moment by making validation and action flow explicit before entry.\n\nNot financial advice. Trading involves risk.\n\n#XeanVI #ExecutionMindset #TradingProcess #DayTrading",
            "image_concept": "A focused product-style interface scene representing decisive execution flow.",
            "image_prompt": "Product screenshot-style mockup with blurred placeholders only, process diagram rendered as abstract boxes and paths, soft monitor glow, cinematic depth and contrast, clean fintech interface-only composition, vertical 1080x1350",
            "negative_prompt": "hands, fingers, face, person, people, human, humans, body, arm, holding, portrait, beard, eyes, detached limbs, malformed anatomy, readable text, fake ticker labels",
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
