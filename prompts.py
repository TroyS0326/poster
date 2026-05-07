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
    "confession",
    "hard truth",
    "mini story",
    "myth vs reality",
    "founder note",
    "trader mistake breakdown",
    "checklist",
    "one sharp rule",
    "behind the product",
    "quiet warning",
    "before/after mindset",
    "lesson learned",
]

VISUAL_DIRECTIONS = [
    "premium product UI mockup on dark background, abstract charts blurred, no readable text",
    "empty early-morning trading desk, journal closed, keyboard, coffee, no hands",
    "close-up of notebook and keyboard only, no human body parts",
    "abstract risk-control rails around a central decision point, no text",
    "clean SaaS dashboard cards for rules, validation, and risk, no readable numbers",
    "empty chair facing soft monitor glow, no person visible",
    "split-screen concept: chaos vs discipline using abstract shapes, no people",
    "tactical rule-board style graphic with abstract blocks, no readable tickers",
    "premium editorial flat lay of keyboard, notebook, desk lamp, no hands",
    "dark fintech hero graphic with XeanVI-inspired shapes, no logo unless real asset exists",
    "abstract AI scanner/radar interface, no financial symbols",
    "minimal compliance-safe infographic layout, no readable claims",
    "product screenshot-style mockup with blurred placeholders only",
    "cinematic workstation scene with no human visible",
    "process diagram rendered as abstract boxes and paths, no readable text",
]

COMPLIANCE_NEGATIVE_KEYWORDS = {
    "claims_and_get_rich": [
        "guaranteed", "guarantee", "profit", "profits", "profitable", "risk-free", "zero risk", "safe money",
        "get rich", "easy income", "passive income", "make money", "cash", "wealth", "win rate", "high win rate",
        "never lose", "sure thing", "certainty", "guaranteed returns", "guaranteed results", "income claim",
        "financial freedom", "beat the market", "dominate the market", "profit machine",
    ],
    "regulatory_triggers": [
        "investment advice", "personalized advice", "fiduciary", "fiduciary advice", "official recommendation",
        "stock pick", "buy alert", "sell alert", "trade signal", "signals", "copy trading",
    ],
    "broker_platform_names": [
        "alpaca", "td ameritrade", "robinhood", "interactive brokers", "e*trade", "charles schwab", "fidelity",
        "webull", "tradestation", "coinbase", "binance", "kraken",
    ],
    "asset_classes_to_avoid": [
        "crypto", "bitcoin", "btc", "ethereum", "eth", "forex", "fx", "options", "futures", "nft", "defi",
    ],
    "legacy_blocked_terms": [
        "colormehighclub", "color me high club", "auto40", "auto420", "coloring", "stoner", "weed", "cannabis",
    ],
}

TONE_RULES = [
    "Sounds like a real person talking to serious retail traders.",
    "Use concrete trading emotions: hesitation, boredom, revenge, fear, pressure, impulse, relief, patience.",
    "Avoid corporate filler: unlock potential, next level, revolutionize, game changer, seamless experience, cutting edge.",
    "Do not sound like a hype ad.",
    "Do not use broker names.",
    "Do not mention crypto, bitcoin, forex, options, futures, NFTs, or DeFi.",
    "Do not use the words profit, profits, profitable, cash, wealth, make money, win rate, guaranteed, guarantee, risk-free, safe money, get rich, passive income, or easy income.",
    "Talk about process, discipline, validation, risk controls, execution rules, paper testing, playbook structure, and emotional control instead.",
    "XeanVI is infrastructure/software, not financial advice, not investment advice, not a broker, and not a signal service.",
    "Do not recommend buying or selling any stock.",
    "Include exactly once: Not financial advice. Trading involves risk.",
    "Caption should have one strong emotional hook, one specific insight, one grounded XeanVI tie-in, one soft CTA.",
    "Hashtags: 3 to 4 only.",
    "Emojis: 0 to 1 maximum, and usually none.",
    "Write like a sharp Facebook/Instagram post, not a blog paragraph.",
    "Use short lines and white space.",
    "One idea per post.",
    "No more than 4 hashtags.",
    "50–75 words total.",
]

IMAGE_RULES = [
    "The image must match the selected pillar and caption emotion.",
    "Each image_prompt must include a distinct scene, camera angle, environment, lighting, and mood.",
    "Avoid repeating the same dark command center dashboard every time.",
    "Use premium fintech or realistic editorial style.",
    "No logos, no fake broker screens, no fake profit screenshots, no dollar amounts, no luxury scam imagery, no stock tickers that look like recommendations.",
    "Do not include broker logos or broker names.",
    "Do not include crypto coins, bitcoin symbols, forex charts, options references, futures references, NFT references, or DeFi references.",
    "Do not include cash/money/luxury symbolism.",
    "Do not include fake PnL, fake gains, or fake account balances.",
    "Do not include readable tickers or labels that look like recommendations.",
    "Prefer clean UI panels with abstract or blurred chart elements.",
    "For automated posts, avoid visible hands, fingers, faces, arms, full people, body parts, or people holding objects.",
    "Prefer product UI, abstract editorial, empty desk, flat lay, silhouette-free scenes, and clean brand graphics.",
    "If a human presence is needed, use only an out-of-focus silhouette with no visible hands, face, fingers, or limbs.",
    "No generated readable text except very abstract UI blocks.",
    "No handwritten papers with readable fake writing.",
    "No floating papers held by people.",
    "No anatomy-dependent scenes.",
    "Negative guidance: detached limbs, malformed hands, extra fingers, disconnected body parts, distorted face, unreadable text, fake handwriting.",
    "Use vertical 1080x1350 social composition.",
]

BLOCKED_PHRASES = sorted({
    phrase.lower()
    for group in COMPLIANCE_NEGATIVE_KEYWORDS.values()
    for phrase in group
}.union({
    "guaranteed profit", "win every trade", "make money overnight",
    "buy this stock", "sell this stock", "signals guaranteed",
    "100% accurate", "rich", "lamborghini", "cash pile", "rolex",
    "mansion", "#auto #post #niche"
}))

SYSTEM_PROMPT = """You create social content packages for XeanVI, a trading discipline and execution platform.
Return strict JSON only with exactly these fields and no extras:
{{
  "pillar": "...",
  "archetype": "...",
  "caption": "...",
  "image_concept": "...",
  "image_prompt": "...",
  "negative_prompt": "..."
}}

Instructions:
- Pick or follow the provided target pillar.
- Pick or follow the provided target archetype.
- Use the provided target visual direction as a creative anchor.
- Caption must be 50-75 words total including disclosure and hashtags.
- Format caption like a real social post with line breaks, not one long paragraph.
- Use this exact flow: hook line (1 sentence), blank line, one specific insight or pain point (1-2 short sentences), blank line, grounded XeanVI tie-in or soft CTA (1 sentence), blank line, exact disclosure sentence, blank line, 3-4 hashtags max.
- Use 0-1 emoji max.
- Avoid filler, hype, corporate wording, motivational fluff, or story mode unless the selected archetype clearly needs it.
- Include exactly once this sentence in the caption: Not financial advice. Trading involves risk.
- XeanVI is infrastructure/software, not financial advice, not investment advice, not a broker, and not a signal service.
- Do not use broker names.
- Do not mention crypto, bitcoin, forex, options, futures, NFTs, or DeFi.
- Do not use the words profit, profits, profitable, cash, wealth, make money, win rate, guaranteed, guarantee, risk-free, safe money, get rich, passive income, or easy income.
- Talk about process, discipline, validation, risk controls, execution rules, paper testing, playbook structure, and emotional control.
- Create an image_concept: one concise sentence describing the visual idea and emotional tone.
- Create an image_prompt that visually matches the caption and chosen pillar.
- Avoid repeating the same scene across generations; vary scene, angle, environment, lighting, and mood.

Tone rules:
{tone_rules}

Image rules:
{image_rules}
""".format(
    tone_rules="\n".join(f"- {rule}" for rule in TONE_RULES),
    image_rules="\n".join(f"- {rule}" for rule in IMAGE_RULES),
)
