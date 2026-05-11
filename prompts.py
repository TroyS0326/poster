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
    {"id": "p1", "allows_text": False, "prompt": "Create a cinematic dark navy and electric blue promotional image for XeanVI, an AI-powered automated trading execution platform for retail day traders. Show a futuristic trading dashboard on a large angled monitor with candlestick charts, live market scan panels, risk status, bot status, active positions, automation log, and rule validation indicators. Use a clean fintech style, high contrast lighting, glowing blue UI accents, premium SaaS branding, no profit guarantees, no clutter, ultra sharp, 16:9 wide banner, abstract UI panels, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p2", "allows_text": False, "prompt": "Create a realistic cinematic image of a focused trader sitting at a modern desk at night, looking at multiple trading screens with candlestick charts, risk controls, and automated playbook validation steps. Add subtle holographic icons showing a playbook, automation gear, rule tree, broker connection, and approval checkmark. Dark office background, blue and teal lighting, professional fintech aesthetic, no exaggerated profits, trustworthy and disciplined trading mood, ultra detailed, 16:9, abstract UI panels, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p3", "allows_text": False, "prompt": "Create a high-end trading command center scene with six monitors showing dark-mode trading dashboards, candlestick charts, market scanner panels, performance analytics, watchlists, order flow, and automation workflow diagrams. Empty chair in front of the desk, modern office environment, moody dark lighting, electric blue accents, realistic screens, clean professional SaaS fintech look, no profit promises, ultra sharp, 1:1 square, abstract UI panels, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p4", "allows_text": False, "prompt": "Create a futuristic AI data pipeline visualization for an automated trading platform. Show a large curved monitor inside a server room displaying a dark-mode workflow for data ingestion, market scanning, preprocessing, feature extraction, playbook rules, risk checks, broker execution, and output analysis. Use electric blue neon lines, technical UI elements, neural network diagram, charts, logs, and system status panels. Premium cybersecurity-fintech style, no profit claims, ultra detailed, 16:9, abstract UI panels, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p5", "allows_text": False, "prompt": "Create a dark premium SaaS hero image for an automated trading bot named XeanVI. Show a sleek dashboard interface with market scanning panels, playbook rule blocks, broker connection modules, risk manager flows, paper trading states, and automation status indicators. Include glowing blue charts, bracket order visualization, stop-loss and target markers, and clear rules-validated style indicators. Clean professional fintech design, trustworthy and disciplined, no guaranteed returns, 16:9, abstract UI panels, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p6", "allows_text": False, "prompt": "Create a realistic professional trader workstation at night with multiple monitors showing algorithmic trading dashboards, scanner results, risk controls, and automated execution logs. Use dark navy, black, electric blue, and teal color grading. The scene should feel disciplined, secure, and professional, like a trading operations command center. No money piles, no luxury lifestyle, no unrealistic claims, ultra realistic, cinematic, 16:9, abstract UI panels, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p7", "allows_text": False, "prompt": "Create a futuristic trading automation interface floating over a dark background. Show candlestick charts, rule validation checklists, broker API connection status, bracket order path, risk limit gauges, and automation timeline logs. Use blue neon highlights, glassmorphism panels, clean UI hierarchy, premium fintech style, high trust, no human faces, no profit guarantees, ultra sharp, 16:9, abstract UI panels, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p8", "allows_text": False, "prompt": "Create a professional social media graphic for XeanVI, an automated trading execution engine. Dark navy background, glowing blue trading dashboard, AI scanner panels, risk manager modules, playbook validation flows, and broker execution status blocks. Premium fintech style, no profit promises, 16:9, abstract UI panels, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
]
VISUAL_DIRECTIONS = [f"template:{p['id']}" for p in IMAGE_PROMPT_TEMPLATES]

DISCLOSURE = "Not financial advice. Trading involves risk."
BRAND_URL = "https://xeanvi.com"
APPROVED_EMOJIS = ["🧠", "⚙️", "📊", "✅", "🛡️", "🔍"]
MONEY_LUXURY_EMOJIS = ["💰", "💸", "🤑", "💎", "🏎️", "🚘", "🛥️", "🛩️", "🏰", "👑"]
HASHTAG_POOL = ["#XeanVI", "#TradingDiscipline", "#RuleBasedExecution", "#RiskControls", "#TradingPlaybook", "#PaperTrading", "#ExecutionDiscipline", "#TradingAutomation", "#DayTrading", "#TradeManagement", "#ProcessOverImpulse", "#TradingRules", "#MarketScanner", "#BracketOrders"]
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
- Do not use “flawless execution,” “perfect setup,” “best strategy,” “smarter execution,” “empower your trading,” or “elevate your trading.”
- Say XeanVI supports rule-following and validation. Do not say it eliminates emotion or guarantees execution quality.
- Prefer grounded phrases: “supports rule-based execution,” “helps enforce user-defined rules,” “keeps validation visible,” “reduces emotional interference.”
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


def build_hashtags(pillar: str, archetype: str, seed: int | None = None) -> list[str]:
    rng = random.Random(seed) if seed is not None else random
    blob = f"{pillar} {archetype}".lower()
    topical_map = {
        "paper": ["#PaperTrading", "#TradingPlaybook", "#TradingRules", "#TradeReview", "#PlaybookFirst"],
        "automation": ["#TradingAutomation", "#RuleBasedExecution", "#ExecutionDiscipline", "#TradingProcess"],
        "scanner": ["#MarketScanner", "#SetupQuality", "#TradingRules", "#TradeManagement"],
        "risk": ["#RiskControls", "#RiskManagement", "#BracketOrders", "#TradingDiscipline"],
        "bracket": ["#BracketOrders", "#TradeManagement", "#RiskControls", "#ExecutionDiscipline"],
        "playbook": ["#TradingPlaybook", "#PlaybookFirst", "#RuleBasedExecution", "#ProcessOverImpulse"],
        "discipline": ["#TradingDiscipline", "#DisciplineOverImpulse", "#TradingProcess", "#TradingRules"],
    }
    pool = [
        "#TradingDiscipline", "#RuleBasedExecution", "#RiskControls", "#TradingPlaybook", "#PaperTrading",
        "#ExecutionDiscipline", "#TradingAutomation", "#DayTrading", "#TradeManagement", "#ProcessOverImpulse",
        "#TradingRules", "#MarketScanner", "#BracketOrders", "#TradingProcess", "#RiskManagement", "#SetupQuality",
        "#TradeReview", "#PlaybookFirst", "#DisciplineOverImpulse",
    ]
    for key, tags in topical_map.items():
        if key in blob:
            pool = list(dict.fromkeys(tags + pool))
            break
    picked = rng.sample(pool, k=3)
    return ["#XeanVI", *picked]


def build_caption(pillar: str, archetype: str, include_url: bool, needs_disclosure: bool, seed: int | None = None) -> str:
    rng = random.Random(seed) if seed is not None else random
    archetype_txt = (archetype or "lesson learned").strip().lower()
    pillar_txt = (pillar or "trading process").strip().lower()

    hooks = {
        "confession": ["I learned this late: activity is not discipline.", "Confession: I used to confuse motion with progress."],
        "hard truth": ["Hard truth: your rules matter most when you want to break them.", "Hard truth: boredom can look like conviction if your process is weak."],
        "mini story": ["A quick story: one impulsive click erased a full week of clean execution.", "Mini story: the setup I skipped saved my process, not my ego."],
        "myth vs reality": ["Myth: more trades means more edge. Reality: better filters create cleaner decisions."],
        "founder note": ["Founder note: we built around pre-commitment, not prediction.", "Founder note: the product starts with your rules, not ours."],
        "trader mistake breakdown": ["Common mistake: changing criteria after the setup appears.", "Mistake breakdown: entries are rarely the first failure; preparation is."],
        "checklist": ["Checklist reminder: if the plan is vague, execution becomes emotional."],
        "one sharp rule": ["One sharp rule: if it fails one rule, it fails the trade."],
        "behind the product": ["Behind the product: every step is designed to keep decision logic visible."],
        "quiet warning": ["Quiet warning: one exception today becomes a pattern tomorrow."],
        "before/after mindset": ["Before: reacting to every candle. After: respecting pre-session criteria."],
        "lesson learned": ["Lesson learned: consistency starts before the first order is considered."],
    }
    insights = [
        "A bad setup does not become better because you are bored.",
        "If your rules disappear under pressure, they were not operational yet.",
        "The trade you skip can be the one that proves your system is working.",
        f"For {pillar_txt}, define invalidation first and decision speed second.",
        "Journal the rejected setups too; that is where discipline compounds.",
    ]
    tie_ins = [
        "XeanVI helps enforce user-defined rules so process quality is visible before execution.",
        "XeanVI supports rule-based execution with validation checkpoints you can review.",
        "XeanVI keeps your playbook checks explicit, so decisions stay tied to defined criteria.",
    ]
    cta_url = [
        f"See how it works: {BRAND_URL}",
        f"Review the workflow at {BRAND_URL}",
    ]
    cta_no_url = [
        "Run your checklist before the market asks for speed.",
        "Protect the process first, then scale execution.",
        "Audit your rules today, not after the session.",
    ]

    hook = rng.choice(hooks.get(archetype_txt, hooks["lesson learned"]))
    emoji = f" {rng.choice(APPROVED_EMOJIS)}" if rng.random() < 0.45 else ""
    hook_line = f"{hook}{emoji}"
    insight_1, insight_2 = rng.sample(insights, k=2)
    tie_in = rng.choice(tie_ins)
    cta = rng.choice(cta_url if include_url else cta_no_url)

    body_lines = [hook_line, "", insight_1, insight_2, "", tie_in, "", cta]
    hashtag_line = " ".join(build_hashtags(pillar, archetype, seed=seed))
    final_caption_without_disclosure = "\n".join([*body_lines, "", hashtag_line]).strip()
    effective_needs_disclosure = needs_disclosure or needs_risk_disclosure(final_caption_without_disclosure)

    lines = list(body_lines)
    if effective_needs_disclosure:
        lines.extend(["", DISCLOSURE])
    lines.extend(["", hashtag_line])
    return "\n".join(lines).strip()


def sanitize_caption_policy(caption: str, needs_disclosure: bool, include_url: bool) -> str:
    text = re.sub(r"\s+", " ", (caption or "")).strip()
    text = re.sub(re.escape(DISCLOSURE), "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\.?\s*Trading involves risk\.", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"Not financial advice\.", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(re.escape(BRAND_URL), "", text, flags=re.IGNORECASE).strip()

    dangling_cta_patterns = [
        r"visit:\s*\.?",
        r"visit\.",
        r"visit at\.",
        r"learn more:\s*\.?",
        r"learn more\.",
        r"learn more at\.",
        r"explore more at\.",
        r"see more at\.",
        r"find out more at\.",
        r"check it out at\.",
        r"go to\.",
        r"go to:",
    ]
    for pattern in dangling_cta_patterns:
        text = re.sub(rf"\b{pattern}", "", text, flags=re.IGNORECASE).strip()

    text = re.sub(r"(?:\s*[.!?,:;]){2,}", ".", text)
    text = re.sub(r"\s+([.!?,:;])", r"\1", text)
    text = re.sub(r"([.!?,:;])\1+", r"\1", text)
    text = re.sub(r"[\s]*([:;,.!?])[\s]*([:;,.!?])", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip(" .:;")

    min_words = 45
    if len(text.split()) < min_words:
        filler = (
            "Explore how XeanVI turns playbook rules into a more disciplined execution workflow. "
            "It helps teams follow pre-defined checks, audit decisions, reduce impulsive actions, "
            "and keep execution aligned with the plan across changing market conditions."
        )
        while len(text.split()) < min_words:
            text = f"{text} {filler}".strip()

    if needs_disclosure:
        text = f"{text} {DISCLOSURE}".strip()
    if include_url:
        text = f"{text} {BRAND_URL}".strip()

    words = text.split()
    if len(words) > 90:
        reserved = 0
        if needs_disclosure:
            reserved += len(DISCLOSURE.split())
        if include_url:
            reserved += 1
        base_limit = max(0, 90 - reserved)
        kept = words[:base_limit]
        if needs_disclosure:
            kept += DISCLOSURE.split()
        if include_url:
            kept += [BRAND_URL]
        text = " ".join(kept[:90])

    text = re.sub(r"\s+", " ", text).strip()
    return text


def repair_caption_compliance(caption: str) -> str:
    text = re.sub(r"\s+", " ", (caption or "")).strip()
    replacements = [
        (r"\bensures flawless execution\b", "supports more consistent rule-following"),
        (r"\bflawless execution\b", "more consistent rule-following"),
        (r"\bexecute with unwavering precision\b", "support more consistent rule-following"),
        (r"\bfreeing you from emotional pitfalls\b", "reducing emotional interference"),
        (r"\bfreeing you from emotion\b", "reducing emotional interference"),
        (r"\bremoving emotional barriers\b", "reducing emotional interference"),
        (r"\bempowers you to transform\b", "helps you turn"),
        (r"\btransform your disciplined approach\b", "turn your defined process"),
        (r"\btransform hesitation into decisive action\b", "Turn hesitation into a more structured review process"),
        (r"\belevate your practice\b", "Build a more structured practice routine"),
        (r"\belevate your trading discipline\b", "Build a more disciplined trading process"),
        (r"\bexplore smarter execution\b", "review a more structured execution workflow"),
        (r"\bsmarter execution\b", "structured execution"),
        (r"\bempower your trading\b", "Build a more disciplined trading process"),
        (r"\bperfect trade setup\b", "qualified setup"),
        (r"\bbest strategies\b", "well-defined strategies"),
        (r"\bmissed opportunities\b", "missed setups"),
        (r"\brisk[- ]free\b", "structured risk controls"),
        (r"\bmake money\b", "improve process discipline"),
        (r"\bwin rate\b", "consistency metrics"),
        (r"\bpassive income\b", "automated workflow"),
        (r"\btrade signal\b", "rule validation"),
        (r"\bsignals\b", "validation workflow"),
        (r"\bbuy/sell alert\b", "execution checklist"),
        (r"\bbuy alert\b", "execution checklist"),
        (r"\bsell alert\b", "execution checklist"),
        (r"\bguaranteed\b", "promised"),
        (r"\bguarantee\b", "promise"),
        (r"\bprofits?\b", "outcomes"),
        (r"\bprofitable\b", "result-oriented"),
        (r"\bwinning virtual trades\b", "passing simulated trades"),
        (r"\bpowerful learning experience\b", "structured review process"),
        (r"\breal capital is on the line\b", "live capital is involved"),
        (r"\bprofit\b", "outcome"),
    ]
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()
