from __future__ import annotations
import os, wave
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from reels.compliance import validate_compliance_text
from reels.config import ReelConfig

SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2

class VoiceoverProvider(Protocol):
    def generate(self, *, config: ReelConfig, output: Path, voice=None, audio_format=None) -> None: ...

def write_silent_wav(output, duration_seconds):
    if output.suffix.lower() != ".wav": raise ValueError("output must end with .wav")
    if duration_seconds <= 0: raise ValueError("duration_seconds must be > 0")
    output.parent.mkdir(parents=True, exist_ok=True)
    frames = int(round(duration_seconds * SAMPLE_RATE))
    with wave.open(str(output), "wb") as w:
        w.setnchannels(CHANNELS); w.setsampwidth(SAMPLE_WIDTH_BYTES); w.setframerate(SAMPLE_RATE)
        rem = frames; chunk = 4096; silence = b"\x00\x00" * chunk
        while rem > 0:
            cur = min(rem, chunk); w.writeframes(silence[:cur * SAMPLE_WIDTH_BYTES]); rem -= cur

@dataclass(frozen=True)
class SilentProvider:
    def generate(self, *, config, output, voice=None, audio_format=None):
        if output.suffix.lower() != ".wav": raise ValueError("silent provider requires .wav")
        write_silent_wav(output, config.duration_seconds)

@dataclass(frozen=True)
class LocalFileProvider:
    def generate(self, *, config, output, voice=None, audio_format=None):
        v = config.voiceover
        if not v or not v.audio_path: raise ValueError("voiceover.audio_path required for local_file")
        src = Path(v.audio_path)
        if not src.exists(): raise FileNotFoundError(f"audio not found: {src}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(src.read_bytes())

@dataclass(frozen=True)
class EdgeTTSOptionalProvider:
    def generate(self, *, config, output, voice=None, audio_format=None):
        v = config.voiceover
        script = (v.script if v else "") or ""
        if not script.strip(): raise ValueError("voiceover.script required for edge_tts_optional")
        validate_compliance_text(script, "voiceover.script")
        try: import edge_tts
        except ImportError as e: raise RuntimeError("install edge-tts: pip install edge-tts") from e
        fmt = (audio_format or output.suffix.lstrip(".") or "mp3").lower()
        if fmt not in {"mp3","wav"}: raise ValueError("edge_tts_optional: mp3 or wav only")
        output.parent.mkdir(parents=True, exist_ok=True)
        import asyncio
        async def _run():
            await edge_tts.Communicate(script, voice or "en-US-AriaNeural").save(str(output))
        asyncio.run(_run())

@dataclass(frozen=True)
class OpenAITTSProvider:
    def generate(self, *, config, output, voice=None, audio_format=None):
        from reels.tts_providers import OpenAITTSProvider as _P
        v = config.voiceover
        script = (v.script if v else "") or ""
        if not script.strip(): raise ValueError("voiceover.script required for openai provider")
        _P().generate(script=script, output=output, voice=voice, audio_format=audio_format)

@dataclass(frozen=True)
class ElevenLabsTTSProvider:
    def generate(self, *, config, output, voice=None, audio_format=None):
        from reels.tts_providers import ElevenLabsTTSProvider as _P
        v = config.voiceover
        script = (v.script if v else "") or ""
        if not script.strip(): raise ValueError("voiceover.script required for elevenlabs provider")
        _P().generate(script=script, output=output, voice=voice, audio_format=audio_format)

def get_provider(name):
    n = (name or "").strip().lower()
    registry = {"silent": SilentProvider(), "local_file": LocalFileProvider(),
                 "edge_tts_optional": EdgeTTSOptionalProvider(),
                 "openai": OpenAITTSProvider(), "elevenlabs": ElevenLabsTTSProvider()}
    if n not in registry:
        raise ValueError(f"unknown provider: '{name}'. Options: {', '.join(sorted(registry))}")
    return registry[n]

def get_default_provider():
    return get_provider(os.getenv("REELS_TTS_PROVIDER", "silent"))
