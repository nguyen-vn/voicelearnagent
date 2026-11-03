"""VoiceLearnAgent: ghép toàn bộ luồng

    Giọng nói ──STT──► Câu hỏi ─┐
    File PDF/ảnh ───────────────┼──► Gemini (+ Google Search) ──► Câu trả lời ──TTS──► Âm thanh
    Câu hỏi gõ phím ────────────┘
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .config import Settings
from .documents import AttachmentError, load_attachments
from .llm import GeminiTutor, LLMAnswer, LLMError, MockTutor
from .prompts import DEFAULT_FILE_REQUEST, build_system_prompt
from .stt import ElevenLabsSTT, MockSTT, STTError
from .text_utils import normalize_question, prepare_for_speech
from .tts import ElevenLabsTTS, MockTTS, TTSError


@dataclass
class TurnResult:
    question: str = ""
    transcript: str = ""
    answer: str = ""
    audio_path: Path | None = None
    sources: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return bool(self.answer)


def build_components(settings: Settings):
    """Chọn provider thật hoặc mock tuỳ theo API key / MOCK_MODE."""
    if settings.voice_mock:
        stt, tts = MockSTT(), MockTTS(settings)
    else:
        stt = ElevenLabsSTT(settings.elevenlabs_api_key, settings.stt_model)
        tts = ElevenLabsTTS(settings)
    tutor = MockTutor() if settings.llm_mock else GeminiTutor(settings.gemini_api_key, settings.gemini_model)
    return stt, tts, tutor


class VoiceLearnAgent:
    def __init__(self, settings: Settings | None = None, stt=None, tts=None, tutor=None):
        self.settings = settings or Settings()
        default_stt, default_tts, default_tutor = (None, None, None)
        if stt is None or tts is None or tutor is None:
            default_stt, default_tts, default_tutor = build_components(self.settings)
        self.stt = stt or default_stt
        self.tts = tts or default_tts
        self.tutor = tutor or default_tutor

    def run(
        self,
        *,
        audio_path: str | None = None,
        text: str | None = None,
        files: list | None = None,
        mode: str = "qa",
        language: str = "vi",
        gender: str = "female",
        use_search: bool = True,
        history: list[dict] | None = None,
        speak: bool = True,
    ) -> TurnResult:
        result = TurnResult()

        # 1) Speech-to-Text (nếu có ghi âm)
        if audio_path:
            try:
                result.transcript = self.stt.transcribe(audio_path, language)
            except STTError as exc:
                result.errors.append(str(exc))

        # 2) Ghép câu hỏi: phần gõ phím + phần nói
        question = " ".join(p for p in [normalize_question(text), normalize_question(result.transcript)] if p)

        # 3) Đọc file đính kèm
        try:
            attachments = load_attachments(files, max_mb=self.settings.max_file_mb)
        except AttachmentError as exc:
            result.errors.append(str(exc))
            attachments = []

        if not question and attachments:
            question = DEFAULT_FILE_REQUEST.get(language, DEFAULT_FILE_REQUEST["vi"]).get(mode, "")
        if not question:
            if not result.errors:
                result.errors.append("Chưa có câu hỏi: hãy ghi âm, gõ câu hỏi hoặc tải file lên.")
            return result
        result.question = question

        # 4) LLM trả lời
        try:
            answer: LLMAnswer = self.tutor.ask(
                question,
                system_prompt=build_system_prompt(mode, language),
                history=(history or [])[-2 * self.settings.history_turns:],
                attachments=attachments,
                use_search=use_search,
            )
        except LLMError as exc:
            result.errors.append(str(exc))
            return result
        result.answer, result.sources = answer.text, answer.sources

        # 5) Text-to-Speech
        if speak:
            try:
                speech_text = prepare_for_speech(result.answer, self.settings.tts_max_chars)
                result.audio_path = self.tts.synthesize(speech_text, language, gender)
            except TTSError as exc:
                result.errors.append(str(exc))
        return result
