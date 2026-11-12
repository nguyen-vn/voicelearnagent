"""App configuration: reads environment variables (.env) and the options shown in the UI."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Supported languages: UI display key -> code used by each API
LANGUAGES = {
    "vi": {"label": "Tiếng Việt", "stt": "vie", "tts": "vi", "name": "Vietnamese"},
    "en": {"label": "English", "stt": "eng", "tts": "en", "name": "English"},
}

GENDERS = {"female": "Nữ / Female", "male": "Nam / Male"}

# Study modes (each mode = a different system prompt, see prompts.py)
MODES = {
    "qa": "Hỏi đáp & giải thích",
    "solve": "Giải bài tập (ảnh/PDF)",
    "summary": "Tóm tắt tài liệu",
    "quiz": "Luyện tập (đố vui)",
}


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


@dataclass
class Settings:
    gemini_api_key: str = field(default_factory=lambda: _env("GEMINI_API_KEY") or _env("GOOGLE_API_KEY"))
    elevenlabs_api_key: str = field(default_factory=lambda: _env("ELEVENLABS_API_KEY"))
    force_mock: bool = field(default_factory=lambda: _env("MOCK_MODE", "0") in {"1", "true", "yes"})

    gemini_model: str = field(default_factory=lambda: _env("GEMINI_MODEL", "gemini-3.8-flash"))
    stt_model: str = field(default_factory=lambda: _env("ELEVENLABS_STT_MODEL", "scribe_v2"))
    tts_model: str = field(default_factory=lambda: _env("ELEVENLABS_TTS_MODEL", "eleven_flash_v2_5"))

    voice_female: str = field(default_factory=lambda: _env("VOICE_FEMALE_ID", "XrExE9yKIg1WjnnlVkGX"))
    voice_male: str = field(default_factory=lambda: _env("VOICE_MALE_ID", "JBFqnCBsd6RMkjVDRZzb"))
    voice_vi_female: str = field(default_factory=lambda: _env("VOICE_VI_FEMALE_ID"))
    voice_vi_male: str = field(default_factory=lambda: _env("VOICE_VI_MALE_ID"))

    tts_max_chars: int = field(default_factory=lambda: int(_env("TTS_MAX_CHARS", "1500") or 1500))
    history_turns: int = 6          # number of most recent conversation turns sent back to the LLM
    max_file_mb: int = 20           # size limit for files sent inline to Gemini
    output_dir: Path = field(default_factory=lambda: ROOT_DIR / "outputs")

    @property
    def llm_mock(self) -> bool:
        return self.force_mock or not self.gemini_api_key

    @property
    def voice_mock(self) -> bool:
        return self.force_mock or not self.elevenlabs_api_key

    def voice_id(self, language: str, gender: str) -> str:
        """Pick a voice ID by (language, gender). Prefers a native Vietnamese voice if one is set."""
        if language == "vi":
            native = self.voice_vi_female if gender == "female" else self.voice_vi_male
            if native:
                return native
        return self.voice_female if gender == "female" else self.voice_male

    def status_text(self) -> str:
        llm = "MOCK" if self.llm_mock else f"Gemini ({self.gemini_model})"
        voice = "MOCK" if self.voice_mock else f"ElevenLabs ({self.stt_model} / {self.tts_model})"
        return f"LLM: {llm} · Voice: {voice}"