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
    {"id": "p1", "allows_text": False, "prompt": "Focused trader during pre-market preparation at a clean desk, writing in a journal beside one monitor with abstract chart shapes and rule-validation panels, soft morning window light, premium editorial photography, disciplined mood, 4:5 vertical social media post, 1080x1350 composition, non-readable interface blocks only, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p2", "allows_text": False, "prompt": "Founder-operator reviewing system health at dusk with a single ultrawide screen showing abstract automation logs, risk controls, and workflow checkpoints, cinematic office lighting, modern professional atmosphere, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos, abstract UI elements only."},
    {"id": "p3", "allows_text": False, "prompt": "Over-the-shoulder trading analysis scene with hands on keyboard and mouse, one monitor displaying abstract scanner signals and structured rule cards, realistic desk textures, high-trust fintech mood, 4:5 vertical social media post, 1080x1350 composition, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p4", "allows_text": False, "prompt": "Calm no-trade discipline visual: tidy desk, empty chair, closed laptop, distant soft chart glow in background, open notebook with non-readable marks, cinematic restraint and patience, premium social composition, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p5", "allows_text": False, "prompt": "Late-night product builder desk with code-like abstract blocks, workflow sketches, and a tablet showing non-readable automation modules, moody blue-gold lighting, documentary editorial style, disciplined build-in-public tone, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p6", "allows_text": False, "prompt": "Premium SaaS dashboard hero for an AI trading execution platform aesthetic, layered glassmorphism panels for scanner, risk, and validation modules, clean depth and contrast, brandable product marketing quality, 4:5 vertical social media post, 1080x1350 composition, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p7", "allows_text": False, "prompt": "Risk-control workflow interface concept with connected cards for entry checks, invalidation logic, size guardrails, and bracket pathways, elegant dark UI with restrained blue accents, high-trust enterprise look, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p8", "allows_text": False, "prompt": "Market scanner and filtering interface visualization: many faint abstract signals narrowed into a few highlighted candidates, radar-inspired circles and panel hierarchy, polished fintech product style, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p9", "allows_text": False, "prompt": "Bracket-order flow illustration with abstract path lines from setup trigger to risk boundary and target zones, minimal dark background, premium UX showcase style, social-ready composition, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p10", "allows_text": False, "prompt": "Rule-validation checklist UI scene with stacked non-readable check modules, subtle status indicators, and disciplined sequence layout, modern product design photography style, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p11", "allows_text": False, "prompt": "Automation timeline and event log concept with abstract time blocks and decision checkpoints, secure operations-center visual tone, crisp cinematic product rendering, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p12", "allows_text": False, "prompt": "Rule-based execution pipeline as geometric rails guiding data from scan to validated action, clean futuristic abstraction with premium blue-neutral palette, high-trust brand campaign quality, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p13", "allows_text": False, "prompt": "Risk guardrails visualized as illuminated geometric barriers around abstract candlestick motion, disciplined and protective mood, modern editorial CGI style, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p14", "allows_text": False, "prompt": "Decision-tree playbook architecture with branching abstract nodes, confidence gates, and validation paths, clean brandable fintech infographic aesthetic without text, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p15", "allows_text": False, "prompt": "Glassmorphism AI workflow panels floating in depth with scanner cards, risk modules, and review stages, elegant lighting and polished gradients, premium social campaign art direction, 4:5 vertical social media post, 1080x1350 composition, non-readable UI blocks only, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p16", "allows_text": False, "prompt": "Cybersecurity and trust system visualization for trading infrastructure, shield-like abstract forms protecting data streams and execution routes, professional enterprise tone, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p17", "allows_text": False, "prompt": "Macro market environment shot with abstract candlestick glow reflected on desk materials, shallow depth of field and cinematic highlights, no tickers or labels, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p18", "allows_text": False, "prompt": "City skyline at blue hour behind a trading desk silhouette, single monitor with non-readable chart shapes, ambitious yet grounded brand mood, editorial photography style, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p19", "allows_text": False, "prompt": "Professional office scene with chart-like reflections on glass walls, analyst workstation in foreground, modern high-trust fintech atmosphere, clean composition for social media, 4:5 vertical social media post, 1080x1350 composition, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p20", "allows_text": False, "prompt": "Desk flat-lay with notebook, keyboard, coffee, tablet, and abstract chart printouts, process-first trading routine aesthetic, soft overhead light, premium editorial still-life, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p21", "allows_text": False, "prompt": "Server-room data pipeline scene with illuminated cables and abstract execution flow overlays, secure infrastructure narrative, cinematic technical realism, 16:9 wide hero layout, non-readable interface blocks, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p22", "allows_text": False, "prompt": "Phone and laptop product preview with synchronized abstract scanner and validation modules, polished hardware lighting and minimal desk context, premium product-marketing quality, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
    {"id": "p23", "allows_text": False, "prompt": "Paper trading lab concept: testing desk with notebook pages, sticky-note-like abstract blocks, keyboard, and tablet arranged as an experiment workflow, calm evidence-based process mood, 4:5 vertical social media post, 1080x1350 composition, no readable writing, no letters, no words, no typography, no logos."},
    {"id": "p24", "allows_text": False, "prompt": "Rejected setup review scene with monitor dimmed, checklist card stack, and journal open to abstract marks, reflective post-session atmosphere emphasizing discipline, cinematic editorial style, 4:5 vertical social media post, 1080x1350 composition, no readable text, no letters, no words, no typography, no logos."},
]
VISUAL_DIRECTIONS = [f"template:{p['id']}" for p in IMAGE_PROMPT_TEMPLATES]

DISCLOSURE = "Not financial advice. Trading involves risk."
BRAND_URL = "https://xeanvi.com"
APPROVED_EMOJIS = ["🧠", "⚙️", "📊", "✅", "🛡️", "🔍"]
MONEY_LUXURY_EMOJIS = ["💰", "💸", "🤑", "💎", "🏎️", "🚘", "🛥️", "🛩️", "🏰", "👑"]
HASHTAG_POOL = ["#XeanVI", "#TradingDiscipline", "#RuleBasedExecution", "#RiskControls", "#TradingPlaybook", "#PaperTrading", "#ExecutionDiscipline", "#TradingAutomation", "#DayTrading", "#TradeManagement", "#ProcessOverImpulse", "#TradingRules", "#MarketScanner", "#BracketOrders"]
RISK_TERMS = {
    "trading", "live trading", "execution", "risk", "bracket orders", "stop-loss", "target", "broker", "order", "scanner", "market",
    "trade", "trades", "no-trade", "setup", "setups", "entry", "entries", "exit", "exits", "loss", "losses", "sizing", "volatility",
    "capital", "live capital", "position", "positions", "invalidation", "stop", "stops", "bracket", "brackets", "trade setup",
    "playbook enforcement",
}
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
        "hesitating": ["#DecisionQuality", "#ExecutionDiscipline", "#ProcessOverImpulse", "#TradeReview"],
        "boredom": ["#Overtrading", "#ProcessOverImpulse", "#TradingRules", "#DisciplineOverImpulse"],
    }
    pool = [
        "#TradingDiscipline", "#RuleBasedExecution", "#RiskControls", "#TradingPlaybook", "#PaperTrading",
        "#ExecutionDiscipline", "#TradingAutomation", "#DayTrading", "#TradeManagement", "#ProcessOverImpulse",
        "#TradingRules", "#MarketScanner", "#BracketOrders", "#TradingProcess", "#RiskManagement", "#SetupQuality",
        "#TradeReview", "#PlaybookFirst", "#DisciplineOverImpulse", "#DecisionQuality", "#PreMarketRoutine",
        "#BehavioralEdge", "#Overtrading", "#RiskFirst",
    ]
    for key, tags in topical_map.items():
        if key in blob:
            pool = list(dict.fromkeys(tags + pool))
            break
    picked = rng.sample(pool, k=3)
    return ["#XeanVI", *picked]


HOOK_BANK = {
    "confession": [
        "Confession: I broke my own rule to avoid being wrong.",
        "Confession: I called it discipline while I was actually hesitating.",
        "Confession: I chased activity when patience was the edge.",
        "Confession: I used to count trades instead of quality.",
        "Confession: one emotional click cost more than a missed setup.",
    ],
    "hard truth": [
        "Hard truth: urgency is usually unplanned risk.",
        "Hard truth: one broken rule can reset a month of progress.",
        "Hard truth: boredom creates fake conviction.",
        "Hard truth: if criteria move, discipline is already gone.",
        "Hard truth: most mistakes are approved before entry.",
    ],
    "mini story": [
        "Mini story: I skipped one setup and kept the whole process intact.",
        "Mini story: the second click was the expensive one.",
        "Mini story: hesitation looked safe until it became a habit.",
        "Mini story: I followed the plan and still had to accept a loss.",
        "Mini story: a no-trade day preserved more than forcing a setup.",
    ],
    "myth vs reality": [
        "Myth: more screen time means better decisions. Reality: better filters do.",
        "Myth: fast reaction is edge. Reality: prepared criteria is edge.",
        "Myth: confidence prevents mistakes. Reality: checklists prevent drift.",
        "Myth: missing a move is failure. Reality: forcing one is.",
        "Myth: automation is prediction. Reality: automation is pre-commitment.",
    ],
    "founder note": [
        "Founder note: we built this from repeated execution mistakes.",
        "Founder note: every feature started as a rule I failed to follow.",
        "Founder note: build-in-public means shipping discipline, not hype.",
        "Founder note: we track decisions, not bravado.",
        "Founder note: the product is opinionated about process integrity.",
    ],
    "trader mistake breakdown": [
        "Mistake breakdown: the setup was fine, the process around it was not.",
        "Mistake breakdown: criteria changed after pressure increased.",
        "Mistake breakdown: the error happened before the order was placed.",
        "Mistake breakdown: size expanded before conviction was earned.",
        "Mistake breakdown: chasing replaced scanning within minutes.",
    ],
    "checklist": [
        "Checklist first: define invalidation before any entry thought.",
        "Checklist first: if one rule fails, the setup fails.",
        "Checklist first: clarity beats speed in volatile sessions.",
        "Checklist first: pre-market decisions protect live decisions.",
        "Checklist first: no criteria, no click.",
    ],
    "one sharp rule": [
        "One sharp rule: no rule, no trade.",
        "One sharp rule: if context changed, reassess before action.",
        "One sharp rule: entries happen only after risk is defined.",
        "One sharp rule: a skipped setup is cheaper than a forced one.",
        "One sharp rule: pause beats panic every time.",
    ],
    "behind the product": [
        "Behind the product: we surface checks before any execution step.",
        "Behind the product: validation is visible on purpose.",
        "Behind the product: the workflow is built around pre-commitment.",
        "Behind the product: discipline features ship before convenience features.",
        "Behind the product: every log line should explain a decision.",
    ],
    "quiet warning": [
        "Quiet warning: exceptions multiply faster than rules.",
        "Quiet warning: today's shortcut becomes tomorrow's baseline.",
        "Quiet warning: hesitation can be as costly as impulsive action.",
        "Quiet warning: emotional relief is not a valid criterion.",
        "Quiet warning: rushed recovery is still overexposure.",
    ],
    "before/after mindset": [
        "Before: I reacted to movement. After: I reacted to criteria.",
        "Before: every candle felt urgent. After: only qualified setups mattered.",
        "Before: I chased confirmation. After: I followed a playbook.",
        "Before: losses triggered speed. After: losses triggered review.",
        "Before: I trusted feeling. After: I trusted process notes.",
    ],
    "lesson learned": [
        "Lesson learned: consistency is built before market open.",
        "Lesson learned: discipline is visible in rejected setups.",
        "Lesson learned: the best reset is fewer low-quality decisions.",
        "Lesson learned: process quality beats session intensity.",
        "Lesson learned: patience is a risk control, not passivity.",
    ],
}

PILLAR_INSIGHTS = {
    "revenge": [("loss", "One bad loss does not deserve a second bad decision."), ("reset", "Reset first, then review the criteria that failed."), ("next_decision", "Your next decision should protect process quality, not ego.")],
    "paper": [("paper", "Paper sessions are worthless if you only track whether you were right."), ("lab", "Treat simulated reps like a lab: hypothesis, execution, review."), ("testing", "Testing without written criteria teaches speed, not discipline.")],
    "automation": [("judgment", "Automation should enforce your rules, not replace your judgment."), ("boundaries", "Good automation applies boundaries you defined before pressure."), ("review", "If you cannot explain the rule, do not automate the action.")],
    "walking": [("walkaway", "No-trade is still a decision when criteria are weak."), ("discipline", "Walking away is a risk control, not a missed opportunity."), ("quality", "Passing on low-quality context protects decision quality.")],
    "bracket": [("bracket", "A bracket is not decoration; it is a pre-commitment."), ("guardrail", "Bracket boundaries reduce negotiation when volatility spikes."), ("riskfirst", "Risk placement belongs before entry excitement.")],
    "playbook": [("playbook", "A playbook is only real when criteria are testable."), ("rules", "Rules should be specific enough to reject most setups."), ("criteria", "Build criteria before capital so pressure has less room to improvise.")],
    "boredom": [("bored", "A bored click is still a rule break."), ("lowquality", "Boredom creates low-quality urgency disguised as opportunity."), ("pace", "If pace is slow, tighten filters instead of forcing activity.")],
    "trust": [("clarity", "Trust grows when claims stay narrower than outcomes."), ("transparency", "Transparency means saying what the system does not do."), ("scope", "Clear scope beats bold promises every time.")],
    "founder": [("build", "Building in public means showing mistakes and iterations."), ("feedback", "Founder updates should include tradeoffs, not only wins."), ("process", "Product decisions are better when users can audit the reasoning.")],
    "scanner": [("scanner", "Scanning is filtering. Chasing is negotiating with FOMO."), ("filter", "A scanner narrows attention to criteria, not excitement."), ("chasing", "Chasing starts when you abandon pre-defined context checks.")],
    "risk": [("risk", "Define risk controls before entries so pressure cannot rewrite them."), ("sequence", "Risk sequence matters: invalidation first, sizing second, entry third."), ("boundary", "Boundaries fail when they are drafted after emotional arousal.")],
    "hesitating": [("hesitation", "Hesitation often means criteria were not pre-committed."), ("decision", "Watching a valid setup pass is data; review why the trigger stalled."), ("confidence", "Confidence comes from repeated criteria execution, not prediction.")],
    "consistency": [("premarket", "Consistency starts in pre-market preparation, not mid-session reactions."), ("routine", "Your opening routine sets the emotional range for the day."), ("check", "A stable process begins with the same checks every session.")],
    "plan": [("plan", "Abandoning the plan early usually starts with one small exception."), ("patience", "Plan adherence is measured when conditions get uncomfortable."), ("execution", "Early deviation compounds into late-session noise.")],
}

GENERAL_INSIGHTS = [
    ("pressure", "Pressure does not create character; it reveals process gaps."),
    ("criteria", "If criteria are vague, emotions will fill the gaps."),
    ("review", "Review is where discipline is rebuilt after difficult sessions."),
    ("risk", "Fast markets punish unclear boundaries first."),
    ("process", "Process quality is measurable in the setups you reject."),
    ("timing", "Speed without structure is still impulsive behavior."),
    ("journal", "A detailed journal turns frustration into actionable adjustments."),
    ("context", "Context checks prevent tunnel vision during momentum spikes."),
    ("prep", "Preparation reduces reaction error when markets accelerate."),
    ("discipline", "Discipline is a sequence of small pre-commitments."),
    ("reset", "A short reset can protect the rest of the session."),
]

FRICTION_LINES = [
    ("urge", "The urge to recover fast is usually the signal to slow down."),
    ("fomo", "FOMO gets louder when your checklist gets quieter."),
    ("fatigue", "Decision fatigue makes average setups look urgent."),
    ("ego", "Ego wants immediate payback; process wants repeatability."),
    ("noise", "Noise feels actionable when boundaries are not explicit."),
    ("speed", "Most rushed clicks begin as unresolved uncertainty."),
    ("drift", "Small rule drift compounds into large execution errors."),
    ("hesitation", "Hesitation grows when entry criteria are not rehearsed."),
]

TIE_INS = [
    "XeanVI helps enforce user-defined rules so process checks stay visible.",
    "XeanVI supports rule-based execution with auditable validation steps.",
    "XeanVI keeps playbook criteria explicit before any execution action.",
    "XeanVI is built to reinforce pre-commitment during live pressure.",
    "XeanVI makes decision checkpoints clear so drift is easier to spot.",
    "XeanVI keeps rule validation in view across the workflow.",
    "XeanVI helps teams review execution against defined criteria.",
    "XeanVI supports structured execution without replacing trader judgment.",
]
CTA_URL = [
    f"See the workflow: {BRAND_URL}",
    f"Review the product notes at {BRAND_URL}",
    f"Explore the platform details: {BRAND_URL}",
    f"Read how the process works: {BRAND_URL}",
    f"Take a look at the build log: {BRAND_URL}",
]
CTA_NO_URL = [
    "Run your checklist before speed asks for shortcuts.",
    "Protect process quality before you chase activity.",
    "Write the rule before you test the setup.",
    "Audit one repeated mistake and remove it this week.",
    "Define your no-trade conditions before the next session.",
    "Review rejected setups and tighten your criteria.",
    "Keep boundaries visible when volatility rises.",
    "Treat patience like an active risk control.",
]
MICRO_STORIES = [
    "I wrote this after a session where one exception became three.",
    "This came from reviewing a week of avoidable clicks.",
    "I used to call this confidence; it was actually urgency.",
    "This note started as a post-loss reset checklist.",
    "I learned this from a no-trade day that saved my process.",
]

SAFE_EXPANSION_LINES = [
    "That makes the review cleaner when pressure shows up.",
    "The goal is fewer improvised decisions under stress.",
    "That keeps the post-session review tied to observable behavior.",
]

WORD_RE = re.compile(r"\b[\w'-]+\b")


def _pillar_key(text: str) -> str:
    t = (text or "").lower()
    checks = [
        ("revenge", ["revenge", "bad loss"]),
        ("plan", ["abandons", "plan too early"]),
        ("paper", ["paper", "testing lab", "simulated"]),
        ("automation", ["automation", "replace judgment"]),
        ("walking", ["walking away", "bad setups"]),
        ("bracket", ["bracket"]),
        ("playbook", ["playbook"]),
        ("boredom", ["boredom", "overtrading"]),
        ("trust", ["trust", "transparency"]),
        ("founder", ["founder", "build-in-public"]),
        ("scanner", ["scanning", "chasing", "scanner"]),
        ("risk", ["risk controls", "before entries"]),
        ("hesitating", ["hesitating", "watching a good setup"]),
        ("consistency", ["consistency", "before the market opens"]),
    ]
    for key, words in checks:
        if any(w in t for w in words):
            return key
    return "plan"


def _caption_word_count(text: str) -> int:
    return len(WORD_RE.findall(text or ""))


def build_caption(pillar: str, archetype: str, include_url: bool, needs_disclosure: bool, seed: int | None = None) -> str:
    rng = random.Random(seed) if seed is not None else random
    archetype_txt = (archetype or "lesson learned").strip().lower()
    pkey = _pillar_key(pillar)

    hook = rng.choice(HOOK_BANK.get(archetype_txt, HOOK_BANK["lesson learned"]))
    if archetype_txt in {"mini story", "confession", "founder note"} and rng.random() < 0.45:
        hook = f"{hook} {rng.choice(MICRO_STORIES)}"
    emoji = f" {rng.choice(APPROVED_EMOJIS)}" if rng.random() < 0.45 else ""
    hook_line = f"{hook}{emoji}"

    pillar_lines = list(PILLAR_INSIGHTS.get(pkey, GENERAL_INSIGHTS))
    first_cat, insight_1 = rng.choice(pillar_lines)

    candidate_second = [x for x in FRICTION_LINES + GENERAL_INSIGHTS if x[0] != first_cat and x[1] != insight_1]
    second_cat, insight_2 = rng.choice(candidate_second)
    if second_cat == first_cat:
        alt = [x for x in candidate_second if x[0] != first_cat]
        if alt:
            _, insight_2 = rng.choice(alt)

    tie_in = rng.choice(TIE_INS)
    cta_source = CTA_URL if include_url else CTA_NO_URL
    cta = rng.choice(cta_source)

    if _caption_word_count(f"{hook_line} {insight_1} {insight_2} {tie_in} {cta}") < 45 and not include_url:
        longer_ctas = [x for x in CTA_NO_URL if _caption_word_count(x) >= 8]
        if longer_ctas:
            cta = rng.choice(longer_ctas)

    body_lines = [hook_line, "", insight_1, insight_2, "", tie_in, "", cta]
    hashtag_line = " ".join(build_hashtags(pillar, archetype, seed=seed))
    final_caption_without_disclosure = "\n".join([*body_lines, "", hashtag_line]).strip()
    effective_needs_disclosure = needs_disclosure or needs_risk_disclosure(final_caption_without_disclosure)

    lines = list(body_lines)
    if effective_needs_disclosure:
        lines.extend(["", DISCLOSURE])
    lines.extend(["", hashtag_line])
    caption = "\n".join(lines).strip()

    wc = _caption_word_count(caption)
    if wc < 45:
        expanded_insight_2 = f"{insight_2} {rng.choice(SAFE_EXPANSION_LINES)}"
        body_lines = [hook_line, "", insight_1, expanded_insight_2, "", tie_in, "", cta]
        final_caption_without_disclosure = "\n".join([*body_lines, "", hashtag_line]).strip()
        effective_needs_disclosure = needs_disclosure or needs_risk_disclosure(final_caption_without_disclosure)
        lines = list(body_lines)
        if effective_needs_disclosure:
            lines.extend(["", DISCLOSURE])
        lines.extend(["", hashtag_line])
        caption = "\n".join(lines).strip()
        wc = _caption_word_count(caption)

    if wc > 90 and " " in hook:
        shorter_hook = hook.split(".")[0].strip()
        if shorter_hook and shorter_hook != hook:
            hook_line = f"{shorter_hook}{emoji}"
            body_lines = [hook_line, "", insight_1, insight_2, "", tie_in, "", cta]
            final_caption_without_disclosure = "\n".join([*body_lines, "", hashtag_line]).strip()
            effective_needs_disclosure = needs_disclosure or needs_risk_disclosure(final_caption_without_disclosure)
            lines = list(body_lines)
            if effective_needs_disclosure:
                lines.extend(["", DISCLOSURE])
            lines.extend(["", hashtag_line])
            caption = "\n".join(lines).strip()

    return caption
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
