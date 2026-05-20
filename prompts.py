import random
import re

# ─────────────────────────────────────────────────────────────────────────────
# CONTENT PILLARS — specific trader pain points, not abstract concepts
# ─────────────────────────────────────────────────────────────────────────────
CONTENT_PILLARS = [
    "You knew the setup was wrong and clicked anyway",
    "Revenge trading after a loss wiped out a winning week",
    "Breaking your stop-loss rule because you were sure it would come back",
    "FOMO entering a move you already missed",
    "Overtrading on a slow day out of boredom",
    "Having a system that works but not being able to follow it",
    "Paper trading showing profit but live trading bleeding money",
    "Letting a winner turn into a loser by not taking profit at target",
    "Adding to a losing position hoping to average down",
    "The emotional spiral after three bad trades in a row",
    "Skipping your pre-market routine and paying for it",
    "Trading without a defined stop and watching it go against you",
    "The difference between traders who last and traders who blow up",
    "Why most traders fail within the first year and how to not be one of them",
]

POST_ARCHETYPES = [
    "brutal honest truth",
    "trader confession",
    "before and after",
    "common mistake breakdown",
    "product feature spotlight",
    "founder story",
    "trader transformation",
    "hard lesson learned",
    "myth vs reality",
    "direct call out",
]

# ─────────────────────────────────────────────────────────────────────────────
# IMAGE PROMPT TEMPLATES — cinematic, specific, no text/faces/hands
# ─────────────────────────────────────────────────────────────────────────────
IMAGE_PROMPT_TEMPLATES = [
    {"id": "p1", "allows_text": False, "prompt": "Cinematic shot of an empty high-end trading workstation at night, three ultrawide curved monitors casting blue glow on dark wood desk, mechanical keyboard, dramatic rim lighting from behind, dark background, hyperrealistic photography, no people, no text on screens, no hands, screens showing abstract dark UI with subtle green and teal glow, 4K commercial photography, vertical 1080x1350 composition"},
    {"id": "p2", "allows_text": False, "prompt": "Dramatic dark fintech control room aesthetic, rows of dark monitors with abstract data visualizations in blue and teal, moody atmospheric lighting, no people visible, no readable text anywhere, cinematic depth of field, premium corporate photography, dark navy and black palette, vertical 1080x1350 composition"},
    {"id": "p3", "allows_text": False, "prompt": "Macro photography of a single sleek trading keyboard with premium RGB lighting in blue and teal, dark desk surface, shallow depth of field, dramatic side lighting, abstract background blur showing monitor glow, no text visible anywhere, luxury tech photography style, vertical 1080x1350 composition"},
    {"id": "p4", "allows_text": False, "prompt": "Abstract 3D visualization of interconnected risk management nodes and pathways, dark background, glowing blue and teal accent lines, geometric precision, futuristic fintech aesthetic, no text, no letters, clean and minimal, premium motion graphics still frame, vertical 1080x1350 composition"},
    {"id": "p5", "allows_text": False, "prompt": "Luxury minimalist trading desk flatlay, dark slate surface, premium laptop with dark abstract screen, wireless earbuds, notebook closed, gold pen, coffee, dramatic overhead lighting with deep shadows, aspirational lifestyle photography, no readable text, no people, vertical 1080x1350 composition"},
    {"id": "p6", "allows_text": False, "prompt": "Cinematic close-up of abstract candlestick chart shapes rendered as 3D glass sculptures on dark background, blue and teal ambient glow, no text labels, no axes, purely visual and artistic, premium CGI render quality, vertical 1080x1350 composition"},
    {"id": "p7", "allows_text": False, "prompt": "Dark atmospheric photograph of a single monitor in a dark room showing abstract teal and blue dashboard wireframe with no readable content, dramatic single light source, moody and focused atmosphere, no people, no hands, cinematic quality, vertical 1080x1350 composition"},
    {"id": "p8", "allows_text": False, "prompt": "Abstract visualization of a decision tree or flowchart rendered as glowing neon lines on pure black background, blue nodes connected by teal pathways, geometric and precise, no text anywhere, premium tech art style, vertical 1080x1350 composition"},
    {"id": "p9", "allows_text": False, "prompt": "High-end trading office at night, empty chair facing panoramic city view through floor-to-ceiling windows, dark interior, ambient blue screen glow, aspirational and solitary mood, cinematic wide shot, no people visible, no text, premium real estate photography quality, vertical 1080x1350 composition"},
    {"id": "p10", "allows_text": False, "prompt": "Abstract geometric composition representing risk and reward balance, dark background, precise angular shapes in navy and teal with gold accent, balanced and structured visual metaphor, no text, premium graphic design quality, vertical 1080x1350 composition"},
    {"id": "p11", "allows_text": False, "prompt": "Cinematic macro shot of premium noise-cancelling headphones on dark leather desk surface, abstract blue monitor glow in background blur, focus and concentration mood, no text visible, luxury product photography, vertical 1080x1350 composition"},
    {"id": "p12", "allows_text": False, "prompt": "Dark dramatic visualization of market data as abstract flowing light streams and particles, blue and teal energy trails on black background, motion blur suggesting speed and complexity, no readable text, premium visual effects quality, vertical 1080x1350 composition"},
    {"id": "p13", "allows_text": False, "prompt": "Premium SaaS dashboard hero shot, dark glassmorphism UI panels floating in depth, blue and teal accent colors, no readable text on any panel, abstract data visualization only, premium product marketing photography, depth of field, vertical 1080x1350 composition"},
    {"id": "p14", "allows_text": False, "prompt": "Atmospheric photograph of a trader's empty desk at dawn, soft morning light through blinds creating dramatic shadow patterns, laptop closed, notebook with pen, coffee steam, anticipation and preparation mood, no people, no readable text anywhere, cinematic still life, vertical 1080x1350 composition"},
    {"id": "p15", "allows_text": False, "prompt": "Abstract 3D render of a shield or protective barrier made of geometric light planes, dark background, blue and teal glow, represents protection and risk control, no text, premium CGI quality, vertical 1080x1350 composition"},
    {"id": "p16", "allows_text": False, "prompt": "Cinematic shot of dark premium smartphone on desk showing abstract dark app interface with teal accents, no readable text on screen, luxury product photography, shallow depth of field, dark background, aspirational fintech aesthetic, vertical 1080x1350 composition"},
    {"id": "p17", "allows_text": False, "prompt": "Abstract visualization of a rule-based system as precise geometric architecture, dark background, glowing blue structural lines, interconnected and organized, represents order versus chaos, no text, architectural visualization quality, vertical 1080x1350 composition"},
    {"id": "p18", "allows_text": False, "prompt": "Moody cinematic photograph of trading workstation from behind, operator silhouette NOT visible, focus on multiple screens showing abstract dark interfaces with subtle colored data, dramatic backlighting, professional trading environment, no text on screens, vertical 1080x1350 composition"},
    {"id": "p19", "allows_text": False, "prompt": "Premium dark background with abstract number streams rendered as vertical light trails, Matrix-inspired but refined and blue/teal instead of green, no readable characters, pure visual texture, dark fintech aesthetic, vertical 1080x1350 composition"},
    {"id": "p20", "allows_text": False, "prompt": "Dramatic close-up of dark mechanical trading keyboard with individual key glow in blue, fingers NOT visible, abstract dark background with monitor glow, luxury tech product photography, no text readable, premium quality, vertical 1080x1350 composition"},
]

VISUAL_DIRECTIONS = [f"template:{p['id']}" for p in IMAGE_PROMPT_TEMPLATES]

# ─────────────────────────────────────────────────────────────────────────────
# BRAND & COMPLIANCE
# ─────────────────────────────────────────────────────────────────────────────
DISCLOSURE = ""
BRAND_URL = "https://xeanvi.com"
APPROVED_EMOJIS = ["🧠", "⚙️", "📊", "✅", "🛡️", "🔍"]
MONEY_LUXURY_EMOJIS = ["💰", "💸", "🤑", "💎", "🏎️", "🚘", "🛥️", "🛩️", "🏰", "👑"]
HASHTAG_POOL = ["#XeanVI", "#TradingDiscipline", "#RuleBasedExecution", "#RiskControls",
                "#TradingPlaybook", "#PaperTrading", "#ExecutionDiscipline", "#TradingAutomation",
                "#DayTrading", "#TradeManagement", "#ProcessOverImpulse", "#TradingRules",
                "#MarketScanner", "#ActiveTrader", "#TradingPsychology", "#RetailTrader",
                "#TradingSystem", "#TradingMindset", "#RiskManagement", "#TradingLife"]

RISK_TERMS = {
    "trading", "live trading", "execution", "risk", "bracket orders", "stop-loss", "target",
    "broker", "order", "scanner", "market", "trade", "trades", "no-trade", "setup", "setups",
    "entry", "entries", "exit", "exits", "loss", "losses", "sizing", "volatility", "capital",
    "live capital", "position", "positions", "invalidation", "stop", "stops", "bracket",
}
URL_CTA_HINTS = {"product", "feature", "website", "signup", "learn more", "try", "explore",
                 "demo", "platform", "free", "start", "join", "get"}

COMPLIANCE_NEGATIVE_KEYWORDS = {
    "claims_and_get_rich": ["guaranteed", "guarantee", "profit", "profits", "profitable",
                            "risk-free", "get rich", "easy income", "passive income",
                            "make money", "cash", "wealth", "win rate"],
    "regulatory_triggers": ["investment advice", "personalized advice", "stock pick",
                            "buy alert", "sell alert", "trade signal", "signals"],
    "broker_platform_names": ["alpaca", "td ameritrade", "robinhood", "interactive brokers",
                              "e*trade", "charles schwab", "fidelity", "webull", "tradestation",
                              "coinbase", "binance", "kraken"],
}
BLOCKED_PHRASES = sorted({p.lower() for g in COMPLIANCE_NEGATIVE_KEYWORDS.values()
                          for p in g}.union({"guaranteed profit", "buy this stock",
                                             "sell this stock", "lamborghini", "mansion", "yacht"}))

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — sales-focused, authentic trader voice
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You create high-converting social media content for XeanVI — a trading execution and discipline platform built for active retail traders.

XeanVI helps traders enforce their own rules before emotions take over. Key features: pre-trade checklists, setup validation, rule-based execution gates, paper testing workflows, execution journaling.

YOUR JOB: Make traders feel seen, build desire for XeanVI, drive them to xeanvi.com.

CONTENT FORMULA:
1. HOOK (1-2 sentences): Name a specific, painful trading mistake traders recognize immediately. Make them feel called out — in a good way.
2. AMPLIFY (1-2 sentences): Dig into why this keeps happening. The real cause — not discipline, but lack of accountability and structure.
3. SOLUTION (1-2 sentences): How XeanVI specifically solves this ONE problem. Name the actual feature. Be specific.
4. CTA (1 sentence): Direct, clear, no fluff.

TONE: Like a successful trader who has been through the pain and found the solution. Real, direct, empathetic — not corporate.

LANGUAGE RULES:
- Write like a person, not a press release
- Short sentences. Impact over length.
- Never say: utilize, leverage, empower, elevate, transform, game-changer, unlock, journey, seamless
- Never make profit or return claims
- Never recommend specific trades or call it financial advice (add disclosure naturally)
- XeanVI is the tool — the trader is still the decision maker

CAPTION LENGTH: 60-100 words total. Punchy wins over thorough.

Return strict JSON only:
{
  "pillar": "...",
  "archetype": "...",
  "caption": "...",
  "image_concept": "...",
  "image_prompt": "...",
  "negative_prompt": "..."
}

image_prompt must be highly specific, cinematic, dark fintech aesthetic, NO text, NO faces, NO hands, NO people. Focus on environment, equipment, abstract visualization, or product UI mockup."""

# ─────────────────────────────────────────────────────────────────────────────
# HOOK BANK — real trader language
# ─────────────────────────────────────────────────────────────────────────────
HOOK_BANK = {
    "brutal honest truth": [
        "Most traders don't have a strategy problem. They have a follow-your-own-strategy problem.",
        "You already know what you're doing wrong. You just can't stop yourself in the moment.",
        "The setup was textbook. You broke your rule anyway. The market punished you for it.",
        "Discipline isn't something you have. It's something you build into your process.",
        "Your system works. You just stop using it when it matters most.",
    ],
    "trader confession": [
        "I've added to losing positions more times than I want to admit.",
        "I've watched a 3R winner turn to a loser because I moved my target. We've all been there.",
        "I used to tell myself I was reading the tape. I was actually just overriding my rules.",
        "I set a stop. The trade went against me. I moved the stop. I know you've done it too.",
        "I built a system that worked on paper. Then live capital hit and everything changed.",
    ],
    "before and after": [
        "Before: broke rules, revenge traded, blew accounts. After: process first, every single time.",
        "Before: 'I'll just move my stop this once.' After: the stop is the stop. Full stop.",
        "Before: trading off feelings. After: trading off a checklist that doesn't have feelings.",
        "Before: knew the setup was wrong, clicked anyway. After: if it doesn't check out, it doesn't happen.",
        "Before: three bad trades, spiral, more bad trades. After: hard limit, walk away, come back tomorrow.",
    ],
    "common mistake breakdown": [
        "Here's how revenge trading destroys a month in a single afternoon:",
        "The most expensive mistake in trading isn't a bad entry. It's not honoring your stop.",
        "Why most traders lose money even with a winning strategy:",
        "The moment you break one rule, breaking the next one gets easier. That's how drawdowns compound.",
        "FOMO is a feeling masquerading as analysis. Here's how to tell the difference:",
    ],
    "product feature spotlight": [
        "XeanVI won't let you enter a trade until your pre-trade checklist is complete.",
        "Every rule you've ever broken in live trading — XeanVI puts a gate in front of it.",
        "Paper test your setup before a single dollar of live capital is at risk. That's XeanVI.",
        "Your entry, your stop, your target — locked in before the emotion starts. That's the point.",
        "XeanVI tracks every rule break so you can see exactly where your process falls apart.",
    ],
    "founder story": [
        "I built XeanVI because I needed it. My discipline failed every time pressure was real.",
        "After blowing my third account I stopped looking for better setups and started building better processes.",
        "I realized the problem wasn't the market. It was me overriding myself at the worst possible moments.",
        "Every feature in XeanVI started as a mistake I made in live trading.",
        "I wanted a tool that held me accountable to the rules I set when I was thinking clearly.",
    ],
    "trader transformation": [
        "The traders who last aren't the ones who find better entries. They're the ones who stop sabotaging good ones.",
        "You can't think your way into discipline under pressure. You have to build it into your system.",
        "Consistency isn't a personality trait for traders. It's a process you build or you don't.",
        "The edge most traders are missing has nothing to do with strategy. It's execution.",
        "The trader you want to be already exists. You just need a system that doesn't let you deviate.",
    ],
    "hard lesson learned": [
        "I learned the hard way: a good setup executed poorly costs more than a missed setup.",
        "The lesson that changed everything: my rules only work if I follow them 100% of the time, not 80%.",
        "Three months of gains. One afternoon of breaking rules. Back to zero. I don't want that for you.",
        "The most painful trades are never the losses. They're the wins that turned into losses.",
        "I stopped blaming the market when I realized every catastrophic loss started with me ignoring my own plan.",
    ],
    "myth vs reality": [
        "Myth: more screen time makes you a better trader. Reality: more process does.",
        "Myth: successful traders have iron willpower. Reality: they have systems that don't rely on it.",
        "Myth: you need a better strategy. Reality: you need to actually follow the one you have.",
        "Myth: professional traders don't feel FOMO. Reality: they built systems that work despite it.",
        "Myth: trading is about prediction. Reality: trading is about execution and risk management.",
    ],
    "direct call out": [
        "If you've broken the same rule more than twice, willpower isn't your solution. Process is.",
        "You wouldn't trust a surgeon who improvises in the operating room. Stop improvising your trades.",
        "That voice saying 'just this once' has cost you more money than any bad setup ever will.",
        "Stop journaling the same mistake. Start building a system that makes it impossible to repeat.",
        "The market doesn't care about your feelings. Build a process that doesn't ask for them.",
    ],
    "myth vs reality": [
        "Myth: more screen time makes you a better trader. Reality: more process does.",
        "Myth: successful traders have iron willpower. Reality: they have systems that don't rely on it.",
        "Myth: you need a better strategy. Reality: you need to actually follow the one you have.",
        "Myth: professional traders don't feel FOMO. Reality: they built systems that work despite it.",
        "Myth: trading is about prediction. Reality: it is about execution and risk management.",
    ],
}

TIE_INS = [
    "XeanVI locks your rules in before emotions can override them.",
    "XeanVI puts a checklist between your feelings and your finger on the trigger.",
    "XeanVI holds you to the standards you set when you were thinking clearly.",
    "XeanVI tracks every deviation so you can see exactly where your process breaks down.",
    "XeanVI validates your setup before you're allowed to enter. Every. Single. Time.",
    "XeanVI is built for the moment discipline fails — which is the moment it matters most.",
    "XeanVI enforces the process you designed before the pressure started.",
]

CTA_URL = [
    f"See how it works at {BRAND_URL}",
    f"Your rules. Enforced. {BRAND_URL}",
    f"Build the process that holds. {BRAND_URL}",
    f"Try XeanVI free at {BRAND_URL}",
    f"Stop fighting yourself. {BRAND_URL}",
]

CTA_NO_URL = [
    "Save this for your next losing streak.",
    "Follow for more on building process over impulse.",
    "Drop a comment if you've been here.",
    "Share this with a trader who needs to hear it.",
    "Follow for daily trading discipline content.",
    "Tag a trader who needs this today.",
]

WORD_RE = re.compile(r"\b[\w'-]+\b")


def needs_risk_disclosure(text_or_pillar: str) -> bool:
    t = (text_or_pillar or "").lower()
    return any(term in t for term in RISK_TERMS)


def should_include_url(pillar: str, archetype: str, seed=None) -> bool:
    blob = f"{pillar} {archetype}".lower()
    if any(hint in blob for hint in URL_CTA_HINTS):
        return True
    rng = random.Random(seed) if seed is not None else random
    return rng.random() < 0.55


def build_hashtags(pillar: str, archetype: str, seed=None) -> list:
    rng = random.Random(seed) if seed is not None else random
    pool = list(HASHTAG_POOL)
    picked = rng.sample(pool[1:], k=3)
    return ["#XeanVI"] + picked


def _caption_word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def build_caption(pillar: str, archetype: str, include_url: bool,
                  needs_disclosure: bool, seed=None) -> str:
    rng = random.Random(seed) if seed is not None else random
    archetype_txt = (archetype or "brutal honest truth").strip().lower()

    hooks = HOOK_BANK.get(archetype_txt, HOOK_BANK["brutal honest truth"])
    hook = rng.choice(hooks)
    tie_in = rng.choice(TIE_INS)
    cta = rng.choice(CTA_URL if include_url else CTA_NO_URL)
    emoji = f" {rng.choice(APPROVED_EMOJIS)}" if rng.random() < 0.4 else ""

    lines = [f"{hook}{emoji}", "", tie_in, "", cta]

    effective_needs_disclosure = False  # removed — software product not financial advisory
    # effective_needs_disclosure = needs_disclosure or needs_risk_disclosure(

    if effective_needs_disclosure:
        lines.extend(["", DISCLOSURE])

    hashtag_line = " ".join(build_hashtags(pillar, archetype, seed=seed))
    lines.extend(["", hashtag_line])

    caption = "\n".join(lines).strip()

    # Enforce word count
    wc = _caption_word_count(caption)
    if wc < 35:
        extra = rng.choice(TIE_INS)
        lines.insert(3, extra)
        caption = "\n".join(lines).strip()

    return caption


def sanitize_caption_policy(caption: str, needs_disclosure: bool,
                             include_url: bool) -> str:
    import re as _re
    text = _re.sub(r"\s+", " ", (caption or "")).strip()
    text = _re.sub(_re.escape(DISCLOSURE), "", text, flags=_re.IGNORECASE).strip()
    text = _re.sub(_re.escape(BRAND_URL), "", text, flags=_re.IGNORECASE).strip()
    text = _re.sub(r"\s+", " ", text).strip(" .:;")

    min_words = 35
    if len(text.split()) < min_words:
        filler = "XeanVI enforces your rules so you can trade your process instead of your emotions."
        while len(text.split()) < min_words:
            text = f"{text} {filler}".strip()

    if needs_disclosure:
        text = f"{text} {DISCLOSURE}".strip()
    if include_url:
        text = f"{text} {BRAND_URL}".strip()

    return _re.sub(r"\s+", " ", text).strip()


def repair_caption_compliance(caption: str) -> str:
    import re as _re
    text = _re.sub(r"\s+", " ", (caption or "")).strip()
    replacements = [
        (r"\bguaranteed?\b", "consistent"),
        (r"\bprofits?\b", "results"),
        (r"\bprofitable\b", "consistent"),
        (r"\brisk[- ]free\b", "lower-risk"),
        (r"\bwin rate\b", "consistency rate"),
        (r"\bpassive income\b", "systematic process"),
        (r"\bmake money\b", "improve consistency"),
        (r"\bget rich\b", "build consistency"),
        (r"\btrade signal\b", "setup validation"),
        (r"\bsignals\b", "validations"),
        (r"\bflawless execution\b", "consistent execution"),
        (r"\bperfect (trade |setup )?\b", "qualified "),
        (r"\bsmarter execution\b", "structured execution"),
        (r"\bempower\b", "support"),
        (r"\belevate\b", "improve"),
        (r"\btransform\b", "improve"),
    ]
    for pattern, replacement in replacements:
        text = _re.sub(pattern, replacement, text, flags=_re.IGNORECASE)
    return _re.sub(r"\s+", " ", text).strip()
