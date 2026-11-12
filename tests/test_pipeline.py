"""Test toàn bộ luồng STT -> LLM -> TTS ở mock mode."""
from conftest import SAMPLES
from voicelearn.llm import LLMError, MockTutor
from voicelearn.pipeline import VoiceLearnAgent
from voicelearn.prompts import build_system_prompt


def test_voice_question_full_flow(settings, wav_file):
    agent = VoiceLearnAgent(settings)
    r = agent.run(audio_path=str(wav_file), language="vi", gender="male")
    assert r.ok and not r.errors
    assert "Quang hợp" in r.transcript
    assert r.audio_path.exists()


def test_file_only_uses_default_request(settings):
    agent = VoiceLearnAgent(settings)
    r = agent.run(files=[str(SAMPLES / "bai_tap_toan.png")], mode="solve", language="vi")
    assert r.question == "Hãy giải bài tập trong tài liệu này."
    call = agent.tutor.calls[0]
    assert call["attachments"][0].name == "bai_tap_toan.png"
    assert "SOLVE EXERCISE" in call["system_prompt"]


def test_text_and_voice_are_combined(settings, wav_file):
    r = VoiceLearnAgent(settings).run(audio_path=str(wav_file), text="Giải thích ngắn gọn:", language="en")
    assert r.question.startswith("Giải thích ngắn gọn:") and "photosynthesis" in r.question


def test_empty_input_returns_friendly_error(settings):
    r = VoiceLearnAgent(settings).run()
    assert not r.ok and r.errors


def test_history_is_trimmed(settings):
    agent = VoiceLearnAgent(settings)
    history = [{"role": "user", "content": f"m{i}"} for i in range(50)]
    agent.run(text="hỏi", history=history)
    assert len(agent.tutor.calls[0]["history"]) == 2 * settings.history_turns


def test_speak_false_skips_tts(settings):
    r = VoiceLearnAgent(settings).run(text="hi", speak=False)
    assert r.ok and r.audio_path is None


def test_llm_error_is_reported(settings):
    class Broken(MockTutor):
        def ask(self, *a, **k):
            raise LLMError("Gemini lỗi: 401")

    r = VoiceLearnAgent(settings, tutor=Broken()).run(text="hi")
    assert not r.ok and "401" in r.errors[0]


def test_system_prompt_language_and_mode():
    p = build_system_prompt("quiz", "en")
    assert "English" in p and "PRACTICE QUIZ" in p
    assert "Vietnamese" in build_system_prompt("qa", "vi")
