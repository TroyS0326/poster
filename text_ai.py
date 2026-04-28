import requests
import random
import json


def _build_prompt(topic):
    return (
        "Write a short, engaging Facebook caption for a brand called XeanVI. "
        f"The topic is {topic}. "
        "Rules: "
        "1. Keep it under 200 characters total. "
        "2. Sound natural and professional. "
        "3. Include exactly 3 trending hashtags at the end. "
        "4. Do not use emojis unless they perfectly fit the tone. "
        "5. Output ONLY the caption and hashtags, no conversational filler."
    )


def _call_gemini(url, headers, prompt):
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code != 200:
        return None

    try:
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip().replace("\n", " ")
    except (KeyError, IndexError):
        return None


def generate_caption(config):
    api_key = config['GEMINI_API_KEY']
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    topics = [
        "new collection drop",
        "premium quality and craftsmanship",
        "streetwear confidence and style",
        "limited release announcement",
    ]
    prompt = _build_prompt(random.choice(topics))

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }
    text = _call_gemini(url, headers, prompt)

    if text and len(text) <= 200:
        return text

    correction_prompt = (
        "Rewrite this caption so it is under 200 characters total and ends with exactly 3 hashtags. "
        "Output only the corrected caption:\n"
        f"{text or ''}"
    )
    corrected = _call_gemini(url, headers, correction_prompt)
    if corrected and len(corrected) <= 200:
        return corrected

    if text:
        return text[:200]

    return "#xeanvi #fashion #style"
