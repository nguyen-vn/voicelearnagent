"""Text-to-Speech: turns the answer into an audio file with ElevenLabs (male / female voice)."""
from __future__ import annotations

import math
import struct
import uuid
import wave
from pathlib import Path

from .config import LANGUAGES, Settings


class TTSError(RuntimeError):
    """Speech synthesis error."""


class ElevenLabsTTS:
    def __init__(self, settings: Settings, client=None):
        if client is None:
            from elevenlabs.client import ElevenLabs

            client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.client = client
        self.settings = settings

    def synthesize(self, text: str, language: str = "vi", gender: str = "female",
                   out_dir: str | Path | None = None) -> Path:
        if not text.strip():
            raise TTSError("Không có nội dung để đọc.")
        out_dir = Path(out_dir or self.settings.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"answer_{uuid.uuid4().hex[:8]}.mp3"

        kwargs = dict(
            voice_id=self.settings.voice_id(language, gender),
            text=text,
            model_id=self.settings.tts_model,
            output_format="mp3_44100_128",
        )
        # language_code helps pronounce Vietnamese correctly (supported by flash_v2_5 / v3)
        if language in LANGUAGES:
            kwargs["language_code"] = LANGUAGES[language]["tts"]
        try:
            chunks = self.client.text_to_speech.convert(**kwargs)  # returns an iterator of byte chunks
            audio = b"".join(chunks)
        except Exception as exc:  # noqa: BLE001
            raise TTSError(f"ElevenLabs TTS lỗi: {exc}") from exc
        if not audio:
            raise TTSError("ElevenLabs không trả về âm thanh.")
        out_path.write_bytes(audio)
        return out_path


class MockTTS:
    """No API call: generates a short 'beep' WAV file (high pitch for female, low for male) to test the flow."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()

    def synthesize(self, text: str, language: str = "vi", gender: str = "female",
                   out_dir: str | Path | None = None) -> Path:
        if not text.strip():
            raise TTSError("Không có nội dung để đọc.")
        out_dir = Path(out_dir or self.settings.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"mock_{uuid.uuid4().hex[:8]}.wav"
        rate, freq = 16000, (440 if gender == "female" else 220)
        seconds = min(2.0, 0.3 + len(text) / 400)
        frames = b"".join(
            struct.pack("<h", int(8000 * math.sin(2 * math.pi * freq * i / rate)))
            for i in range(int(rate * seconds))
        )
        with wave.open(str(out_path), "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(rate)
            w.writeframes(frames)
        return out_path