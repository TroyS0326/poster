from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from reels.compliance import validate_compliance_text
from reels.config import ReelConfig
import wave

SAMPLE_RATE = 44100
CHANNELS = 1
SAMPLE_WIDTH_BYTES = 2


def write_silent_wav(output: Path, duration_seconds: float) -> None:
    if output.suffix.lower() != ".wav":
        raise ValueError("output path must end with .wav")
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")

    output.parent.mkdir(parents=True, exist_ok=True)
    frame_count = int(round(duration_seconds * SAMPLE_RATE))

    with wave.open(str(output), "wb") as wav_file:
        wav_file.setnchannels(CHANNELS)
        wav_file.setsampwidth(SAMPLE_WIDTH_BYTES)
        wav_file.setframerate(SAMPLE_RATE)
        remaining_frames = frame_count
        chunk_frames = 4096
        silence_chunk = b"\x00\x00" * chunk_frames
        while remaining_frames > 0:
            current = min(remaining_frames, chunk_frames)
            wav_file.writeframes(silence_chunk[: current * SAMPLE_WIDTH_BYTES])
            remaining_frames -= current


class VoiceoverProvider(Protocol):
    def generate(self, *, config: ReelConfig, output: Path, voice: str | None = None, audio_format: str | None = None) -> None:
        ...


@dataclass(frozen=True)
class SilentProvider:
    def generate(self, *, config: ReelConfig, output: Path, voice: str | None = None, audio_format: str | None = None) -> None:
        if output.suffix.lower() != ".wav":
            raise ValueError("silent provider requires output path ending in .wav")
        write_silent_wav(output, config.duration_seconds)


@dataclass(frozen=True)
class LocalFileProvider:
    def generate(self, *, config: ReelConfig, output: Path, voice: str | None = None, audio_format: str | None = None) -> None:
        voiceover = config.voiceover
        if voiceover is None or not voiceover.audio_path:
            raise ValueError("voiceover.audio_path is required for provider local_file")
        src = Path(voiceover.audio_path)
        if not src.exists():
            raise FileNotFoundError(f"local_file provider source audio not found: {src}")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(src.read_bytes())


@dataclass(frozen=True)
class EdgeTTSOptionalProvider:
    def generate(self, *, config: ReelConfig, output: Path, voice: str | None = None, audio_format: str | None = None) -> None:
        voiceover = config.voiceover
        script = (voiceover.script if voiceover else "") or ""
        script = script.strip()
        if not script:
            raise ValueError("voiceover.script is required for provider edge_tts_optional")
        validate_compliance_text(script, "voiceover.script")

        try:
            import edge_tts  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "edge_tts_optional provider requires optional dependency 'edge-tts'. Install it to enable real TTS."
            ) from exc

        fmt = (audio_format or output.suffix.lstrip(".") or "mp3").lower()
        if fmt not in {"mp3", "wav"}:
            raise ValueError("edge_tts_optional supports only mp3 or wav output format")

        if not output.suffix:
            output = output.with_suffix(f".{fmt}")
        output.parent.mkdir(parents=True, exist_ok=True)

        selected_voice = voice or "en-US-AriaNeural"

        import asyncio

        async def _run() -> None:
            communicate = edge_tts.Communicate(script, selected_voice)
            await communicate.save(str(output))

        asyncio.run(_run())


def get_provider(name: str) -> VoiceoverProvider:
    normalized = name.strip().lower()
    if normalized == "silent":
        return SilentProvider()
    if normalized == "local_file":
        return LocalFileProvider()
    if normalized == "edge_tts_optional":
        return EdgeTTSOptionalProvider()
    raise ValueError(f"unsupported voiceover provider: {name}")
