import random
import re

CONTENT_PILLARS = [
    "Revenge trading after one bad loss",
    "The trader who abandons their plan too early",
    "Paper trading as a serious testing lab, not a toy",
    "Why automation should enforce rules, not replace judgment",
    "The quiet discipline of walking away from bad setups",
    "Bracket orders as emotional guardrails",
    "Building a playbook before live capital",
    "Overtrading from boredom",
    "Trust/transparency: what XeanVI does and does not claim",
    "Founder/build-in-public: building the tool I wish I had",
    "The difference between scanning and chasing",
    "Risk controls before entries",
    "The pain of watching a good setup and hesitating",
    "Why consistency starts before the market opens",
]

POST_ARCHETYPES = [
    "confession", "hard truth", "mini story", "myth vs reality", "founder note",
    "trader mistake breakdown", "checklist", "one sharp rule", "behind the product",
    "quiet warning", "before/after mindset", "lesson learned",
]

IMAGE_PROMPT_TEMPLATES = [
    {"id": "p1", "allows_text": True, "prompt": "Create a cinematic dark navy and electric blue promotional image for XeanVI, an AI-powered automated trading execution platform for retail day traders. Show a futuristic trading dashboard on a large angled monitor with candlestick charts, live market scan panels, risk status, bot status, active positions, automation log, and rule validation indicators. Add bold professional text: \"AUTOMATE. EXECUTE. TRADE WITH DISCIPLINE.\" Use a clean fintech style, high contrast lighting, glowing blue UI accents, premium SaaS branding, no profit guarantees, no clutter, ultra sharp, 16:9 wide banner."},
    {"id": "p2", "allows_text": False, "prompt": "Create a realistic cinematic image of a focused trader sitting at a modern desk at night, looking at multiple trading screens with candlestick charts, risk controls, and automated playbook validation steps. Add subtle holographic icons showing a playbook, automation gear, rule tree, broker connection, and approval checkmark. Dark office background, blue and teal lighting, professional fintech aesthetic, no text, no exaggerated profits, trustworthy and disciplined trading mood, ultra detailed, 16:9."},
    {"id": "p3", "allows_text": False, "prompt": "Create a high-end trading command center scene with six monitors showing dark-mode trading dashboards, candlestick charts, market scanner panels, performance analytics, watchlists, order flow, and automation workflow diagrams. Empty chair in front of the desk, modern office environment, moody dark lighting, electric blue accents, realistic screens, clean professional SaaS fintech look, no text, no profit promises, ultra sharp, 1:1 square."},
    {"id": "p4", "allows_text": False, "prompt": "Create a futuristic AI data pipeline visualization for an automated trading platform. Show a large curved monitor inside a server room displaying a dark-mode flowchart: data ingestion, market scanning, preprocessing, feature extraction, playbook rules, risk checks, broker execution, and output analysis. Use electric blue neon lines, technical UI elements, neural network diagram, charts, logs, and system status panels. Premium cybersecurity-fintech style, no text branding, no profit claims, ultra detailed, 16:9."},
    {"id": "p5", "allows_text": False, "prompt": "Create a dark premium SaaS hero image for an automated trading bot named XeanVI. Show a sleek dashboard interface with sections labeled market scanner, playbook rules, broker connection, risk manager, paper trading, and automation status. Include glowing blue charts, bracket order visualization, stop-loss and target markers, and a clear rules validated style status indicator. Clean professional fintech design, trustworthy, disciplined, no guaranteed returns, 16:9."},
    {"id": "p6", "allows_text": False, "prompt": "Create a realistic professional trader workstation at night with multiple monitors showing algorithmic trading dashboards, scanner results, risk controls, and automated execution logs. Use dark navy, black, electric blue, and teal color grading. The scene should feel disciplined, secure, and professional, like a trading operations command center. No money piles, no luxury lifestyle, no unrealistic claims, no text, ultra realistic, cinematic, 16:9."},
    {"id": "p7", "allows_text": False, "prompt": "Create a futuristic trading automation interface floating over a dark background. Show candlestick charts, rule validation checklists, broker API connection status, bracket order path, risk limit gauges, and automation timeline logs. Use blue neon highlights, glassmorphism panels, clean UI hierarchy, premium fintech branding style, high trust, no human faces, no profit guarantees, ultra sharp, 16:9."},
    {"id": "p8", "allows_text": True, "prompt": "Create a professional social media graphic for XeanVI, an automated trading execution engine. Dark navy background, glowing blue trading dashboard, AI scanner panel, risk manager module, playbook validation flow, and broker execution status. Add headline text: \"YOUR PLAYBOOK. YOUR RULES. AUTOMATED EXECUTION.\" Add small footer text: \"Your account. Your funds. Your control.\" Premium fintech style, clean typography, no profit promises, 16:9."},
]
VISUAL_DIRECTIONS = [f"template:{p['id']}" for p in IMAGE_PROMPT_TEMPLATES]

DISCLOSURE = "Not financial advice. Trading involves risk."
BRAND_URL = "https://xeanvi.com"
RISK_TERMS = {"trading", "live trading", "execution", "risk", "bracket orders", "stop-loss", "target", "broker", "order", "scanner", "market", "entries", "exits", "trade setup", "playbook enforcement"}
URL_CTA_HINTS = {"product", "feature", "website", "signup", "learn more", "try", "explore", "demo", "platform"}

COMPLIANCE_NEGATIVE_KEYWORDS = {
    "claims_and_get_rich": ["guaranteed", "guarantee", "profit", "profits", "profitable", "risk-free", "get rich", "easy income", "passive income", "make money", "cash", "wealth", "win rate"],
    "regulatory_triggers": ["investment advice", "personalized advice", "stock pick", "buy alert", "sell alert", "trade signal", "signals"],
    "broker_platform_names": ["alpaca", "td ameritrade", "robinhood", "interactive brokers", "e*trade", "charles schwab", "fidelity", "webull", "tradestation", "coinbase", "binance", "kraken"],
}
BLOCKED_PHRASES = sorted({p.lower() for g in COMPLIANCE_NEGATIVE_KEYWORDS.values() for p in g}.union({"guaranteed profit", "buy this stock", "sell this stock", "lamborghini", "mansion", "yacht"}))

SYSTEM_PROMPT = """You create social content packages for XeanVI, a trading discipline and execution platform.
Return strict JSON only with exactly these fields and no extras:
{
  \"pillar\": \"...\",
  \"archetype\": \"...\",
  \"caption\": \"...\",
  \"image_concept\": \"...\",
  \"image_prompt\": \"...\",
  \"negative_prompt\": \"...\"
}

Instructions:
- Pick or follow the provided target pillar.
- Pick or follow the provided target archetype.
- Use the provided target visual direction as a creative anchor.
- Caption must be 45-90 words.
- Use one strong hook, one insight, one XeanVI tie-in, and one CTA.
- Use the disclosure only when the post discusses trading risk, execution, orders, market scanning, broker connection, or live trading behavior.
- Include https://xeanvi.com only when the selected CTA is product/website/signup oriented.
- Do not include the URL in every post.
- Do not use profit, profits, profitable, guaranteed, guarantee, passive income, win rate, risk-free, get rich, make money, easy income.
- Do not call XeanVI a signal service.
- Do not recommend trades.
- Automation enforces user-defined rules; it does not replace judgment.
- Allow readable headline text only when using a template that explicitly includes text.
- Never include URLs inside image_prompt.
"""

def needs_risk_disclosure(text_or_pillar: str) -> bool:
    t = (text_or_pillar or "").lower()
    return any(term in t for term in RISK_TERMS)


def should_include_url(pillar: str, archetype: str, seed: int | None = None) -> bool:
    blob = f"{pillar} {archetype}".lower()
    if any(hint in blob for hint in URL_CTA_HINTS):
        return True
    rng = random.Random(seed) if seed is not None else random
    return rng.random() < 0.42


def sanitize_caption_policy(caption: str, needs_disclosure: bool, include_url: bool) -> str:
    text = re.sub(r"\s+", " ", (caption or "")).strip()
    text = re.sub(re.escape(DISCLOSURE), "", text, flags=re.IGNORECASE).strip()
    text = re.sub(re.escape(BRAND_URL), "", text, flags=re.IGNORECASE).strip()
    if needs_disclosure:
        text = f"{text} {DISCLOSURE}".strip()
    if include_url:
        text = f"{text} {BRAND_URL}".strip()
    words = text.split()
    if len(words) > 90:
        text = " ".join(words[:90])
    return text
