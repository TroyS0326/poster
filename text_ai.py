import requests
import random
import os
import json

# Optimized, humanized, <220-char caption, ONLY trending hashtags returned
def generate_caption(config):
    api_key = config['GEMINI_API_KEY']
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

    prompts = [
        # Strict prompt for Gemini - short, natural, <220 chars, only trending hashtags, nothing else
        (
            "Enter your prompt "
            "Here. make sure"
            "Every line is formatted like this"
            "****************************************************************************************************************** "
            "**************************************************************************************************************************"
            "**********************************************"
        ),
        (
            "Enter your prompt "
            "Here. make sure"
            "Every line is formatted like this"
            "****************************************************************************************************************** "
            "**************************************************************************************************************************"
            "**********************************************"
        ),
    ]
    prompt = random.choice(prompts)

    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        result = response.json()
        try:
            # Only return the caption itself (strip newlines, ensure under 220 chars)
            text = result["candidates"][0]["content"]["parts"][0]["text"].strip().replace('\n', ' ')
            if len(text) > 220:
                text = text[:219]
            return text
        except (KeyError, IndexError):
            return "#auto #post #niche"
    else:
        return "#auto #post #niche"
