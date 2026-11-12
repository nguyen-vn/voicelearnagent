import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from voicelearn.config import Settings  # noqa: E402
from voicelearn.tts import MockTTS  # noqa: E402

SAMPLES = ROOT / "samples"


@pytest.fixture
def settings(tmp_path):
    """Settings luôn ở mock mode, ghi file ra thư mục tạm."""
    return Settings(gemini_api_key="", elevenlabs_api_key="", force_mock=True, output_dir=tmp_path)


@pytest.fixture
def wav_file(settings):
    """Một file wav nhỏ đóng vai 'ghi âm câu hỏi'."""
    return MockTTS(settings).synthesize("xin chào", out_dir=settings.output_dir)


# ---------- Fake SDK clients (giả lập đúng hình dạng API thật) ----------
class FakeGenaiClient:
    def __init__(self, text="Câu trả lời từ Gemini.", with_sources=False, error=None):
        self.requests = []
        chunks = [SimpleNamespace(web=SimpleNamespace(uri="https://vi.wikipedia.org/wiki/Quang_hợp",
                                                     title="Wikipedia"))] if with_sources else None
        self._response = SimpleNamespace(
            text=text,
            candidates=[SimpleNamespace(grounding_metadata=SimpleNamespace(grounding_chunks=chunks))],
        )
        self._error = error
        self.models = SimpleNamespace(generate_content=self._generate)

    def _generate(self, **kwargs):
        self.requests.append(kwargs)
        if self._error:
            raise self._error
        return self._response


class FakeElevenClient:
    def __init__(self, transcript="Quang hợp là gì?", audio=b"ID3fake-mp3"):
        self.stt_calls, self.tts_calls = [], []
        self._transcript, self._audio = transcript, audio
        self.speech_to_text = SimpleNamespace(convert=self._stt)
        self.text_to_speech = SimpleNamespace(convert=self._tts)

    def _stt(self, **kwargs):
        self.stt_calls.append(kwargs)
        return SimpleNamespace(text=self._transcript)

    def _tts(self, **kwargs):
        self.tts_calls.append(kwargs)
        return iter([self._audio[:3], self._audio[3:]])  # SDK trả về iterator các chunk bytes


@pytest.fixture
def fake_genai():
    return FakeGenaiClient


@pytest.fixture
def fake_eleven():
    return FakeElevenClient
