"""Test lớp gọi API thật (Gemini / ElevenLabs) bằng client giả – không tốn tiền, không cần mạng."""
import pytest

from conftest import SAMPLES
from voicelearn.documents import load_attachment
from voicelearn.llm import GeminiTutor, LLMError
from voicelearn.stt import ElevenLabsSTT, STTError
from voicelearn.tts import ElevenLabsTTS, TTSError


# ---------- Gemini ----------
def test_gemini_builds_request_with_history_file_and_search(fake_genai):
    client = fake_genai(with_sources=True)
    tutor = GeminiTutor("key", "gemini-test", client=client)
    history = [{"role": "user", "content": "Xin chào"}, {"role": "assistant", "content": "Chào bạn"}]
    ans = tutor.ask("Giải bài 1", system_prompt="SYS", history=history,
                    attachments=[load_attachment(SAMPLES / "bai_tap_toan.png")], use_search=True)

    req = client.requests[0]
    assert req["model"] == "gemini-test"
    roles = [c.role for c in req["contents"]]
    assert roles == ["user", "model", "user"]
    last_parts = req["contents"][-1].parts
    assert last_parts[0].inline_data.mime_type == "image/png"     # file đi trước câu hỏi
    assert last_parts[-1].text == "Giải bài 1"
    assert req["config"].system_instruction == "SYS"
    assert req["config"].tools[0].google_search is not None
    assert ans.text == "Câu trả lời từ Gemini."
    assert ans.sources == [{"title": "Wikipedia", "url": "https://vi.wikipedia.org/wiki/Quang_hợp"}]


def test_gemini_without_search_has_no_tools(fake_genai):
    client = fake_genai()
    GeminiTutor("key", client=client).ask("hi", system_prompt="S", use_search=False)
    assert client.requests[0]["config"].tools is None


def test_gemini_errors_are_wrapped(fake_genai):
    with pytest.raises(LLMError):
        GeminiTutor("k", client=fake_genai(error=RuntimeError("429 quota"))).ask("q", system_prompt="s")
    with pytest.raises(LLMError):
        GeminiTutor("k", client=fake_genai(text="")).ask("q", system_prompt="s")


# ---------- ElevenLabs STT ----------
def test_stt_passes_model_and_language(fake_eleven, wav_file):
    client = fake_eleven()
    text = ElevenLabsSTT("k", "scribe_v2", client=client).transcribe(wav_file, "vi")
    assert text == "Quang hợp là gì?"
    call = client.stt_calls[0]
    assert call["model_id"] == "scribe_v2" and call["language_code"] == "vie"


def test_stt_empty_transcript_raises(fake_eleven, wav_file):
    with pytest.raises(STTError):
        ElevenLabsSTT("k", client=fake_eleven(transcript="  ")).transcribe(wav_file, "en")


# ---------- ElevenLabs TTS ----------
@pytest.mark.parametrize("gender,expected", [("female", "F_ID"), ("male", "M_ID")])
def test_tts_picks_voice_and_writes_mp3(fake_eleven, settings, gender, expected):
    settings.voice_female, settings.voice_male = "F_ID", "M_ID"
    client = fake_eleven()
    path = ElevenLabsTTS(settings, client=client).synthesize("Xin chào", "vi", gender)
    assert path.suffix == ".mp3" and path.read_bytes() == b"ID3fake-mp3"
    call = client.tts_calls[0]
    assert call["voice_id"] == expected and call["language_code"] == "vi"
    assert call["model_id"] == settings.tts_model


def test_tts_prefers_native_vietnamese_voice(settings):
    settings.voice_vi_male = "VI_MALE"
    assert settings.voice_id("vi", "male") == "VI_MALE"
    assert settings.voice_id("en", "male") == settings.voice_male


def test_tts_empty_text_raises(fake_eleven, settings):
    with pytest.raises(TTSError):
        ElevenLabsTTS(settings, client=fake_eleven()).synthesize("   ")
