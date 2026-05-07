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
    "early morning desk with trading journal, coffee, soft monitor glow",
    "close-up of handwritten playbook rules beside a keyboard",
    "tense trader pausing before clicking, cinematic over-shoulder",
    "abstract risk-control system with bracket rails, clean fintech aesthetic",
    "paper trading lab concept, sandbox testing environment, charts blurred",
    "minimal dark UI rule-builder screen, no fake profit numbers",
    "calm workstation after market close, notes and reflection",
    "split scene: chaos/chasing vs discipline/playbook",
    "AI scanner as subtle radar/map interface, not a profit machine",
    "professional SaaS product mockup with cards for rules, risk, validation",
    "empty chair, monitors glowing, system follows rules when emotions spike mood",
    "tactical command board with risk limits, stop-loss, target zones, neutral numbers only",
    "macro photo of keyboard, notebook, and simple rule card",
    "founder build-in-public desk with code/editor and trading workflow diagrams",
    "clean educational infographic style, no fake logos and no readable financial claims",
]

TONE_RULES = [
    "Sounds like a real person talking to serious retail traders.",
    "Use concrete trading emotions: hesitation, boredom, revenge, fear, pressure, impulse, relief, patience.",
    "Avoid corporate filler: unlock potential, next level, revolutionize, game changer, seamless experience, cutting edge.",
    "Do not sound like a hype ad.",
    "Do not claim XeanVI makes traders profitable.",
    "Do not say or imply guaranteed outcomes.",
    "Do not recommend buying or selling any stock.",
    "Include exactly once: Not financial advice. Trading involves risk.",
    "Caption should have one strong emotional hook, one specific insight, one grounded XeanVI tie-in, one soft CTA.",
    "Hashtags: 3 to 5 only.",
    "Emojis: 0 to 1 maximum, and usually none.",
]

IMAGE_RULES = [
    "The image must match the selected pillar and caption emotion.",
    "Each image_prompt must include a distinct scene, camera angle, environment, lighting, and mood.",
    "Avoid repeating the same dark command center dashboard every time.",
    "Use premium fintech or realistic editorial style.",
    "No logos, no fake broker screens, no fake profit screenshots, no dollar amounts, no luxury scam imagery, no stock tickers that look like recommendations.",
    "Prefer clean UI panels with abstract or blurred chart elements.",
    "Use vertical 1080x1350 social composition.",
]

BLOCKED_PHRASES = [
    "guaranteed profit", "risk-free", "win every trade", "make money overnight",
    "buy this stock", "sell this stock", "signals guaranteed",
    "100% accurate", "passive income", "rich", "lamborghini", "cash pile", "rolex",
    "mansion", "colormehighclub", "color me high club", "auto40", "auto420",
    "coloring", "stoner", "weed", "cannabis", "#auto #post #niche"
]

SYSTEM_PROMPT = """You create social content packages for XeanVI, a trading discipline and execution platform.
Return strict JSON only with exactly these fields and no extras:
{
  "pillar": "...",
  "archetype": "...",
  "caption": "...",
  "image_concept": "...",
  "image_prompt": "...",
  "negative_prompt": "..."
}

Instructions:
- Pick or follow the provided target pillar.
- Pick or follow the provided target archetype.
- Use the provided target visual direction as a creative anchor.
- Create an original caption that is 300-850 characters and sounds human, specific, and grounded.
- Include exactly once this sentence in the caption: Not financial advice. Trading involves risk.
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
