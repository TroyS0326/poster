CONTENT_PILLARS = [
    "Discipline Over Emotion",
    "Trading Playbook Education",
    "Paper Trading / Testing Before Live",
    "Broker API / Automation Concepts",
    "Risk Management / Bracket Orders",
    "AI Market Scanning",
    "Founder / Build-in-public style XeanVI posts",
    "Common retail trader mistakes",
    "Platform trust / transparency posts",
    "Short punchy rules beat emotion posts",
]

BLOCKED_PHRASES = [
    "guaranteed profit", "risk-free", "win every trade", "make money overnight",
    "buy this stock", "sell this stock", "financial advice", "signals guaranteed",
    "100% accurate", "passive income", "rich", "lamborghini", "cash pile", "rolex",
    "mansion", "colormehighclub", "color me high club", "auto40", "auto420",
    "coloring", "stoner", "weed", "cannabis", "#auto #post #niche"
]

SYSTEM_PROMPT = """You create social posts for XeanVI, a trading discipline and execution platform. Return strict JSON only:
{"pillar":"...","caption":"...","image_prompt":"...","negative_prompt":"..."}
Caption rules: 350-900 chars, strong hook, one value point, soft CTA, 3-7 relevant hashtags, 0-2 emojis, no hype, no guarantees, no stock picks, no advice. Optional: Not financial advice. Trading involves risk.
Image prompt rules: premium fintech dark-mode command center visuals, realistic, no fake profits, no luxury scam imagery, no logos.
"""
