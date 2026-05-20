from __future__ import annotations
import os
from pathlib import Path
from reels.compliance import validate_compliance_text

def _clean_script(script: str) -> str:
    """Strip spoken-pause markers that TTS engines read aloud."""
    import re
    script = re.sub(r"\((?:short |long )?pause\)", " ", script, flags=re.I)
    script = re.sub(r"\[(?:short |long )?pause\]", " ", script, flags=re.I)
    script = re.sub(r"<break[^>]*>", " ", script, flags=re.I)
    script = re.sub(r"\s{2,}", " ", script)
    return script.strip()


class OpenAITTSProvider:
    def generate(self, *, script, output, voice=None, audio_format=None):
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError("Run: pip install openai") from e
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise ValueError("OPENAI_API_KEY required")
        script = _clean_script(script)
        if not script:
            raise ValueError("script must not be empty")
        validate_compliance_text(script, "tts_script")
        selected_voice = (voice or os.getenv("OPENAI_TTS_VOICE", "onyx")).strip().lower()
        model = os.getenv("OPENAI_TTS_MODEL", "tts-1-hd").strip()
        ext = output.suffix.lower().lstrip(".") or "mp3"
        fmt = audio_format or ext
        if fmt not in {"mp3", "opus", "aac", "flac", "wav", "pcm"}:
            fmt = "mp3"
        output.parent.mkdir(parents=True, exist_ok=True)
        client = OpenAI(api_key=api_key)
        response = client.audio.speech.create(model=model, voice=selected_voice, input=script, response_format=fmt)
        response.stream_to_file(str(output))

class ElevenLabsTTSProvider:
    VOICES = {"adam": "pNInz6obpgDQGcFmaJgB", "josh": "TxGEqnHWrfWFTfGW9XjX",
              "rachel": "21m00Tcm4TlvDq8ikWAM", "domi": "AZnzlk1XvdvUeBnXmlld"}
    def generate(self, *, script, output, voice=None, audio_format=None):
        import requests as _req
        api_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY required — get one at elevenlabs.io")
        script = _clean_script(script)
        if not script:
            raise ValueError("script must not be empty")
        validate_compliance_text(script, "tts_script")
        raw = (voice or os.getenv("ELEVENLABS_VOICE_ID", "adam")).strip().lower()
        voice_id = self.VOICES.get(raw, raw) or self.VOICES["adam"]
        model_id = os.getenv("ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5").strip()
        output.parent.mkdir(parents=True, exist_ok=True)
        resp = _req.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers={"xi-api-key": api_key, "Content-Type": "application/json", "Accept": "audio/mpeg"},
            json={"text": script, "model_id": model_id,
                  "voice_settings": {"stability": 0.55, "similarity_boost": 0.80,
                                     "style": 0.20, "use_speaker_boost": True}},
            timeout=120)
        if resp.status_code == 401: raise ValueError("ElevenLabs key invalid")
        if resp.status_code == 429: raise RuntimeError("ElevenLabs rate limit hit")
        if not resp.ok: raise RuntimeError(f"ElevenLabs error {resp.status_code}: {resp.text[:200]}")
        output.write_bytes(resp.content)
