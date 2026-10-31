"""Cấu hình ứng dụng: đọc biến môi trường (.env) và các lựa chọn trên giao diện."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

# Ngôn ngữ hỗ trợ: key hiển thị trên UI -> mã dùng cho từng API
LANGUAGES = {
    "vi": {"label": "Tiếng Việt", "stt": "vie", "tts": "vi", "name": "Vietnamese"},
    "en": {"label": "English", "stt": "eng", "tts": "en", "name": "English"},
}

GENDERS = {"female": "Nữ / Female", "male": "Nam / Male"}

# Chế độ học tập (mỗi chế độ = một system prompt khác nhau, xem prompts.py)
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
    history_turns: int = 6          # số lượt hội thoại gần nhất gửi lại cho LLM
    max_file_mb: int = 20           # giới hạn dung lượng file gửi inline cho Gemini
    output_dir: Path = field(default_factory=lambda: ROOT_DIR / "outputs")

    @property
    def llm_mock(self) -> bool:
        return self.force_mock or not self.gemini_api_key

    @property
    def voice_mock(self) -> bool:
        return self.force_mock or not self.elevenlabs_api_key

    def voice_id(self, language: str, gender: str) -> str:
        """Chọn voice ID theo (ngôn ngữ, giới tính). Ưu tiên giọng bản ngữ tiếng Việt nếu có."""
        if language == "vi":
            native = self.voice_vi_female if gender == "female" else self.voice_vi_male
            if native:
                return native
        return self.voice_female if gender == "female" else self.voice_male

    def status_text(self) -> str:
        llm = "MOCK" if self.llm_mock else f"Gemini ({self.gemini_model})"
        voice = "MOCK" if self.voice_mock else f"ElevenLabs ({self.stt_model} / {self.tts_model})"
        return f"LLM: {llm} · Voice: {voice}"
