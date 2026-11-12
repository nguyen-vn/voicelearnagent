"""Speech-to-Text: converts audio recordings to text using ElevenLabs Scribe."""
from __future__ import annotations

from pathlib import Path

from .config import LANGUAGES


class STTError(RuntimeError):
    """Speech recognition error."""


class ElevenLabsSTT:
    def __init__(self, api_key: str, model: str = "scribe_v2", client=None):
        if client is None:
            from elevenlabs.client import ElevenLabs

            client = ElevenLabs(api_key=api_key)
        self.client = client
        self.model = model

    def transcribe(self, audio_path: str | Path, language: str | None = "vi") -> str:
        """language = 'vi' | 'en' | None (None = auto-detect the language)."""
        audio_path = Path(audio_path)
        if not audio_path.exists():
            raise STTError(f"Không tìm thấy file âm thanh: {audio_path}")
        lang_code = LANGUAGES[language]["stt"] if language in LANGUAGES else None
        try:
            with audio_path.open("rb") as f:
                result = self.client.speech_to_text.convert(
                    file=f,
                    model_id=self.model,
                    language_code=lang_code,
                    tag_audio_events=False,  # no need for audio event tags (laughter...)
                )
        except Exception as exc:  # noqa: BLE001
            raise STTError(f"ElevenLabs STT lỗi: {exc}") from exc
        text = (getattr(result, "text", "") or "").strip()
        if not text:
            raise STTError("Không nghe rõ câu hỏi. Bạn hãy nói lại gần micro hơn nhé.")
        return text


class MockSTT:
    """No API call: returns a sample question to test the flow."""

    SAMPLES = {
        "vi": "Quang hợp là gì và diễn ra ở đâu trong cây?",
        "en": "What is photosynthesis and where does it happen in a plant?",
    }

    def transcribe(self, audio_path, language: str | None = "vi") -> str:
        if not audio_path or not Path(audio_path).exists():
            raise STTError(f"Không tìm thấy file âm thanh: {audio_path}")
        return self.SAMPLES.get(language or "vi", self.SAMPLES["vi"])