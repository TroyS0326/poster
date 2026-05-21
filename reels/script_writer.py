"""
Elite trading reel script writer.
Engineered to trigger FB/IG algorithmic signals:
  Private Shares > Saves > Deep Comments > Watch Time
Every script is built on proven viral frameworks used by top trading creators.
"""
from __future__ import annotations
import os, re, logging, random
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT — this is what separates viral from forgettable
# ─────────────────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are the best trading content writer on social media in 2026.
Your content gets shared to group chats. Traders screenshot your hooks and send them to friends.
Your videos get 80%+ completion rates because every second earns the next.

YOUR VOICE:
- Battle-tested trader who has blown up accounts and rebuilt
- Direct, specific, zero fluff — like texting a trader friend at 2am after a bad session  
- Never preachy. Never motivational poster. Never corporate.
- Speaks in SPECIFICS: "$2,340 loss" not "big loss". "Tuesday at market open" not "recently"
- Uses trader slang naturally: "got chopped up", "revenge traded", "sized up wrong", "stopped out"
- Occasionally uses mild emphasis (not profanity) — "I was dead wrong", "this wrecked me"

PSYCHOLOGICAL TRIGGERS YOU ALWAYS HIT:
1. IDENTITY: Make the viewer feel seen — "you know that feeling when..."
2. SPECIFICITY: Fake details feel fake. Real numbers feel real. Always use odd numbers.
3. PATTERN INTERRUPT: Say something in the first 2 seconds that breaks their scroll trance
4. CURIOSITY GAP: Start a story they MUST finish to understand
5. SOCIAL PROOF INVERSION: "Every trader I know does X — and they all lose because of it"
6. LOSS AVERSION: Pain of losing > pleasure of winning. Lead with loss.

WHAT GOES VIRAL IN 2026:
- Content that makes people think "I need to send this to my trading group"
- Specific confessions: "I did this exact thing 3 weeks ago and it cost me my week"
- Contrarian takes that feel TRUE once you hear them
- Behind-the-scenes moments that feel like you accidentally saw something real
- The "dark truth" format: what the industry doesn't want you to know

ABSOLUTE RULES:
1. HOOK = first 5-8 words MAX. Must work as a standalone sentence that stops thumbs.
2. NEVER write: journey, game-changer, level up, dive in, unpack, let's talk about, 
   here's the thing, you know what I mean, at the end of the day, in today's video,
   I'm going to show you, make sure to, follow for more, smash that like button
3. Total script: 65-95 words. Spoken in 18-30 seconds naturally.
4. Every sentence must earn the next. If it doesn't add tension or information — cut it.
5. Use SPECIFIC numbers: not "most traders" — "7 out of 10 traders I've talked to this month"
6. End with ONE sharp sentence about XEANVI that feels like a natural conclusion, not an ad
7. No pause markers. No stage directions. Just the words a real trader would say.
8. Write for SILENCE — most people watch with no sound. Every line must land as text too."""


# ─────────────────────────────────────────────────────────────────────────────
# THE 5 VIRAL FRAMEWORKS — each engineered for specific algorithm signals
# ─────────────────────────────────────────────────────────────────────────────
FRAMEWORKS = {
    "direct_problem": {
        "name": "Direct Problem + Hard Rule",
        "signal": "SAVES — viewers bookmark this because it's a rule they want to remember",
        "hook_template": "State a specific hard rule as absolute fact. Make it feel like a warning.",
        "examples": [
            "If your trading system has no hard daily loss limit, you don't have a system.",
            "The moment you move a stop loss, you've already lost — the money just hasn't left yet.",
            "3% account risk per trade sounds conservative. After 5 losses it's a margin call.",
        ],
        "body": "Prove the rule with a specific scenario. Use exact numbers. Show the math of how it destroys accounts. End with how the rule saves you.",
        "cta_angle": "XEANVI enforces the rules when your emotions won't.",
    },
    "insider_truth": {
        "name": "The Dark Truth Nobody Says",
        "signal": "PRIVATE SHARES — people send this to their trading group",
        "hook_template": "Reveal something the industry actively hides or ignores.",
        "examples": [
            "Your broker makes more money when you overtrade. Think about that.",
            "The trading educators selling you courses are profitable from courses, not trading.",
            "Nobody talks about this: consistency beats a 70% win rate every single time.",
        ],
        "body": "Connect the dark truth to the viewer's personal experience. Make them feel like they've been lied to — and that you're the one finally being honest.",
        "cta_angle": "XEANVI was built because the industry won't build it for you.",
    },
    "confession": {
        "name": "Raw Confession / I Was Wrong",
        "signal": "DEEP COMMENTS — people share their own confession in the comments",
        "hook_template": "Open with a specific personal failure. First person. Specific date or amount.",
        "examples": [
            "I turned $8,400 into $1,200 in 6 trading days. Here's the exact sequence.",
            "Last Thursday I broke every rule I wrote myself. Twice. In the same session.",
            "I watched a $4,100 winner become a $680 loser because I didn't have a rule.",
        ],
        "body": "Walk through the exact failure moment by moment. What you were thinking. What you did. The specific number it cost. Then the lesson that came from it.",
        "cta_angle": "XEANVI is the system I wish I had before that day.",
    },
    "contrarian": {
        "name": "Contrarian Scroll-Stop",
        "signal": "COMPLETION RATE — viewers stay to see if you can prove it",
        "hook_template": "Attack a belief every trader holds. Make it sound insane but provable.",
        "examples": [
            "Having a winning strategy is actually making your trading worse.",
            "The traders losing the most money right now are the ones studying the hardest.",
            "More screen time does not make you a better trader. It makes you worse.",
        ],
        "body": "Prove the contrarian take with specific logic. Address the objection they're already forming. Land the twist that makes it click.",
        "cta_angle": "XEANVI is built on this exact principle.",
    },
    "numbered_list": {
        "name": "Number + Specific Outcome",
        "signal": "WATCH TIME — viewers stay to hear all items, completion rate spikes",
        "hook_template": "Lead with a specific number and a painful outcome. Odd numbers perform best.",
        "examples": [
            "3 things profitable traders do differently that nobody teaches.",
            "The 4 exact moments I've blown up accounts — and the pattern I finally noticed.",
            "5 rules I wish I had year one. Number 3 would have saved me $11,000.",
        ],
        "body": "Deliver each item fast. One punchy sentence per item. Number them out loud. Make each one feel like its own revelation. Save the most painful/surprising for last.",
        "cta_angle": "XEANVI handles every single one of these automatically.",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# PAIN PILLARS — 14 specific trader wounds we target
# ─────────────────────────────────────────────────────────────────────────────
PAIN_PILLARS = [
    "revenge trading after a loss",
    "moving stop losses hoping to avoid the hit",
    "sizing up after winners then giving it all back",
    "watching a setup work perfectly after you second-guessed it",
    "breaking your own written rules in real time",
    "overtrading on slow days out of boredom",
    "knowing exactly what to do and doing the opposite",
    "letting a winner turn into a loser by holding too long",
    "trading FOMO — entering late because you fear missing it",
    "having a winning strategy but losing money anyway",
    "paper trading perfectly, live trading terribly",
    "starting strong then blowing the week in one session",
    "adding to losing positions and making it catastrophic",
    "quitting a system that would have worked if you trusted it",
]


def _select_framework(topic: str, pain: str) -> dict:
    t = f"{topic} {pain}".lower()
    if any(w in t for w in ["confession", "blew", "lost", "mistake", "wrong", "cost me"]):
        return FRAMEWORKS["confession"]
    if any(w in t for w in ["nobody", "truth", "industry", "secret", "broker", "educator"]):
        return FRAMEWORKS["insider_truth"]
    if any(w in t for w in ["3 ", "4 ", "5 ", "number", "list", "biggest", "mistakes"]):
        return FRAMEWORKS["numbered_list"]
    if any(w in t for w in ["backwards", "wrong", "actually", "counterintuitive", "more"]):
        return FRAMEWORKS["contrarian"]
    if any(w in t for w in ["rule", "system", "cap", "limit", "discipline", "process"]):
        return FRAMEWORKS["direct_problem"]
    return random.choice(list(FRAMEWORKS.values()))


def generate_script(topic: str, pain_pillar: str, scenes: list[str]) -> str:
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    except Exception as e:
        logger.warning("Gemini unavailable: %s", e)
        return _elite_fallback(topic, pain_pillar)

    fw = _select_framework(topic, pain_pillar)
    scene_txt = "\n".join(f"Scene {i+1}: {s}" for i, s in enumerate(scenes))

    prompt = f"""Write a viral trading reel voiceover script.

TOPIC: {topic}
TRADER PAIN THIS TARGETS: {pain_pillar}
SCENES:
{scene_txt}

USE THIS FRAMEWORK: {fw['name']}
Algorithm signal this targets: {fw['signal']}
Hook approach: {fw['hook_template']}
Hook examples to INSPIRE (don't copy): 
{chr(10).join(f'  • {e}' for e in fw['examples'])}
Body approach: {fw['body']}
CTA angle: {fw['cta_angle']}

WRITE THE SCRIPT NOW.
Requirements:
- First 6 words must make someone stop scrolling cold
- Use ONE specific made-up-but-believable number (dollar amount, percentage, or timeframe)
- 65-95 words total
- Raw trader voice — like a DM from a friend who just figured something out
- Last sentence naturally names XEANVI as the answer without sounding like an ad
- ZERO pause markers, stage directions, or labels — pure voiceover text only"""

    try:
        model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            system_instruction=SYSTEM_PROMPT,
        )
        result = model.generate_content(prompt)
        script = result.text.strip()
        # Nuclear option — strip any markers that snuck through
        script = re.sub(r'\((?:short |long )?pause\)', ' ', script, flags=re.I)
        script = re.sub(r'\[(?:short |long )?pause\]', ' ', script, flags=re.I)
        script = re.sub(r'\*+([^*]+)\*+', r'\1', script)   # strip markdown bold
        script = re.sub(r'#{1,3}\s*', '', script)            # strip headers
        script = re.sub(r'\s{2,}', ' ', script).strip()
        word_count = len(script.split())
        logger.info("Script generated: %d words, framework=%s", word_count, fw['name'])
        return script
    except Exception as e:
        logger.warning("Gemini failed: %s", e)
        return _elite_fallback(topic, pain_pillar)


def _elite_fallback(topic: str, pain: str) -> str:
    """Fallbacks that are still elite quality — not generic filler."""
    fallbacks = [
        f"Most traders with a winning strategy still blow up. Not because the strategy failed. Because they couldn't execute it the same way twice. One loss turns into revenge. Revenge turns into a ruined week. The strategy was never the problem — the consistency was. XEANVI is the layer between your emotions and your execution. It's what I wish existed three years ago.",

        f"Here's what nobody tells you about trading discipline. It doesn't exist under pressure. Every rule you write when you're calm gets broken the second you're down $800 and the market looks like it's reversing. You're not weak. You're human. That's why XEANVI builds the rules into the process itself — so your emotions don't get a vote.",

        f"The 3 things that will end your trading career: sizing up after a big win. Averaging into a loser. Moving your stop one more time. Every trader knows this. Every trader has done all three in the same session. XEANVI enforces the rules when your conviction is at its most dangerous.",
    ]
    return random.choice(fallbacks)


# ── Compatibility wrapper — storyboard.py calls this name ────────────────────
def generate_reel_script(topic: str) -> dict | None:
    """
    Called by storyboard.py. Returns structured dict with hook/problem/insight/cta
    AND a full voiceover script. Returns None on failure so storyboard falls back.
    """
    try:
        import google.generativeai as genai
        import os, re
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])

        fw = _select_framework(topic, topic)

        prompt = f"""Write a viral trading reel script for this topic: {topic}

Use the "{fw['name']}" framework.
Hook style: {fw['hook_template']}
Hook examples (inspire only, don't copy): {fw['examples'][0]}

Return ONLY a JSON object with these exact keys — no markdown, no explanation:
{{
  "hook": "5-8 word scroll-stopping opening line",
  "problem": "1-2 sentence specific pain point with a real number",
  "insight": "1-2 sentence truth/turn that reframes the problem",
  "cta": "1 sentence natural XEANVI mention as the solution",
  "voiceover": "full 65-90 word script combining all four parts naturally"
}}

Rules:
- hook must work as a standalone sentence that stops thumbs
- use ONE specific believable number somewhere (dollar amount, percentage, days)
- raw trader voice — like a DM at 2am after a bad session
- NO pause markers, NO stage directions, NO markdown in the values
- voiceover is plain text only, natural sentences, no labels"""

        model = genai.GenerativeModel(
            model_name=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            system_instruction=SYSTEM_PROMPT,
        )
        resp = model.generate_content(prompt)
        text = resp.text.strip()

        # Strip markdown code fences if present
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.M)
        text = re.sub(r'\s*```$', '', text, flags=re.M)

        import json
        data = json.loads(text.strip())

        # Strip pause markers from every field
        for key in ["hook", "problem", "insight", "cta", "voiceover"]:
            if key in data:
                val = data[key]
                val = re.sub(r'\((?:short |long )?pause\)', ' ', val, flags=re.I)
                val = re.sub(r'\[(?:short |long )?pause\]', ' ', val, flags=re.I)
                val = re.sub(r'\s{2,}', ' ', val).strip()
                data[key] = val

        logger.info("generate_reel_script OK — framework=%s hook=%s", fw['name'], data.get('hook','')[:40])
        return data

    except Exception as e:
        logger.warning("generate_reel_script failed: %s", e)
        return None
