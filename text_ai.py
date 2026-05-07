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
            "caption": "One red trade can flip your brain from patient to reckless in seconds. That revenge click feels like control, but it is usually just pain wearing a strategy mask. XeanVI is built to force a pause: validate your setup, respect your risk bracket, then decide if the trade still makes sense. If your pulse is leading, step back before risk size goes up. Not financial advice. Trading involves risk. #XeanVI #TradingPsychology #RiskManagement",
            "image_concept": "A tense pause moment before an emotional re-entry, emphasizing restraint over impulse.",
            "image_prompt": "Cinematic over-shoulder scene of a trader's hand hovering above mouse after a recent losing trade, risk checklist card in foreground, muted monitor glow, shallow depth of field, late afternoon desk environment, serious restrained mood, premium fintech editorial realism, abstract blurred charts only, vertical 1080x1350",
            "negative_prompt": "fabricated performance screens, platform branding, flashy lifestyle props, currency imagery, readable market symbols, hype text, low detail, cartoon",
        },
        {
            "pillar": "The trader who abandons their plan too early",
            "archetype": "lesson learned",
            "caption": "Most plan failures are not bad plans, they are early exits under pressure. You define rules at 7:30 AM, then fear rewrites them at 9:47 AM. XeanVI helps keep execution tied to your preplanned logic so panic does not become policy. If your system says wait, waiting is the trade. Not financial advice. Trading involves risk. #DayTrading #ExecutionDiscipline #XeanVI",
            "image_concept": "A visual contrast between written premarket rules and in-session emotional hesitation.",
            "image_prompt": "Macro photo of handwritten entry and exit rules beside mechanical keyboard, blurred monitor in background with neutral chart shapes, cool morning window light, clean desk texture, reflective mood, realistic editorial photography, vertical 1080x1350 composition",
            "negative_prompt": "readable market symbols, fabricated performance visuals, flashy neon overload, promotional banners, brand marks, currency symbols",
        },
        {
            "pillar": "Paper trading as a serious testing lab, not a toy",
            "archetype": "myth vs reality",
            "caption": "Myth: paper trading is fake, so it does not matter. Reality: sloppy paper habits become expensive live habits. Treat simulation like a lab: log setup quality, rule adherence, and exit behavior. XeanVI leans into this by validating process before pressure capital is involved. Practice is only useful when it is structured. Not financial advice. Trading involves risk. #PaperTrading #TradingProcess #XeanVI",
            "image_concept": "A controlled lab-like environment for testing trading rules before live deployment.",
            "image_prompt": "Modern sandbox-style trading lab concept, clean workstation with notebook labeled test cases, blurred chart panels on side monitor, neutral grayscale and teal palette, soft overhead lighting, analytical calm mood, premium fintech design language, vertical 1080x1350",
            "negative_prompt": "casino-like visuals, jackpot imagery, fabricated platform interface, outcome promises, recommendation-style labels, high saturation meme style",
        },
        {
            "pillar": "Why automation should enforce rules, not replace judgment",
            "archetype": "founder note",
            "caption": "I did not build XeanVI to replace trader judgment. I built it because judgment gets distorted when stress spikes and speed compresses decisions. Automation should handle rule enforcement, not ego. Your edge still comes from preparation, context, and restraint. The tool just helps your rules survive the moment. Not financial advice. Trading involves risk. #BuildInPublic #TradingSystems #XeanVI",
            "image_concept": "Founder desk scene showing human decision-making supported by structured automation.",
            "image_prompt": "Founder workspace with code editor and workflow diagram notes, one monitor showing abstract rule validation cards, warm desk lamp mixed with cool screen light, intentional clutter, thoughtful late-night mood, realistic fintech editorial style, vertical 1080x1350",
            "negative_prompt": "robot-trader fantasy, certainty slogans, oversized performance numbers, brand marks, glamour-office styling",
        },
        {
            "pillar": "The quiet discipline of walking away from bad setups",
            "archetype": "one sharp rule",
            "caption": "A setup that almost fits is still a no. The hardest discipline is doing nothing when boredom begs for action. XeanVI reinforces this by making rule misses visible before you commit capital, so passing becomes an active decision, not a missed chance. Protecting your focus is part of protecting your account. Not financial advice. Trading involves risk. #TradingDiscipline #RuleBasedTrading #XeanVI",
            "image_concept": "Calm restraint after rejecting a low-quality setup.",
            "image_prompt": "Empty ergonomic trading chair facing softly glowing monitors after market close, closed notebook with checklist tick marks on desk, gentle dusk lighting, quiet reflective atmosphere, minimal premium fintech aesthetic, vertical social framing 1080x1350",
            "negative_prompt": "celebration scene, confetti, outcome claims, readable market-symbol labels, fabricated performance widgets",
        },
        {
            "pillar": "Bracket orders as emotional guardrails",
            "archetype": "checklist",
            "caption": "Before entry, define the exit framework: stop, target, invalidation. Bracket structure is less about prediction and more about emotional containment once the position is live. XeanVI keeps those guardrails front and center so heat-of-the-moment edits are harder to justify. Rules are boring, and that is why they work. Not financial advice. Trading involves risk. #RiskControl #BracketOrders #XeanVI",
            "image_concept": "An abstract yet practical depiction of risk boundaries around a trade plan.",
            "image_prompt": "Clean fintech interface concept with three labeled abstract zones for stop, target, invalidation, layered as guardrails around a central entry point, isometric camera angle, cool charcoal palette with subtle cyan accents, focused technical mood, no numbers or tickers, vertical 1080x1350",
            "negative_prompt": "price-prediction visuals, rocket emojis, fabricated account panels, brand marks, cluttered casino-like aesthetics",
        },
        {
            "pillar": "Overtrading from boredom",
            "archetype": "quiet warning",
            "caption": "Boredom can be more dangerous than volatility. When nothing clean is there, the mind starts inventing setups just to feel productive. XeanVI helps by forcing setup criteria back into view before execution, so impulse has to argue with your own rules first. Some of your best days are the ones with fewer clicks. Not financial advice. Trading involves risk. #Overtrading #TraderMindset #XeanVI",
            "image_concept": "A split emotional scene showing impulsive clicking versus disciplined waiting.",
            "image_prompt": "Split composition: left side chaotic rapid clicking and scribbled notes, right side composed trader reviewing structured playbook checklist, contrast lighting from harsh red tones to calm blue tones, cinematic documentary style, strong emotional duality, vertical 1080x1350",
            "negative_prompt": "binary-style promo vibe, certainty claims, market-symbol tips, glamour props, misleading performance charts",
        },
        {
            "pillar": "The pain of watching a good setup and hesitating",
            "archetype": "mini story",
            "caption": "You spot the setup, everything aligns, then hesitation freezes your hand for five seconds too long. That sting is real, and repeating it can quietly erode confidence. XeanVI cannot remove emotion, but it can sharpen pre-trade clarity so execution is less ambiguous when the moment arrives. Confidence usually comes from process, not hype. Not financial advice. Trading involves risk. #Execution #TradingPsychology #XeanVI",
            "image_concept": "A high-tension pre-click moment where clarity and hesitation collide.",
            "image_prompt": "Over-the-shoulder close shot of trader pausing before clicking execution button (text unreadable), focus on tense hand posture, dim studio-like trading room with single monitor glow, moody cinematic lighting, emotionally charged but professional fintech realism, vertical 1080x1350",
            "negative_prompt": "visible recommendation labels, oversized performance visuals, certainty slogans, brand marks, meme graphics, poor anatomy",
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
