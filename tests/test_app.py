"""Smoke test giao diện: build được UI và hàm xử lý trả đúng số output."""
import os

os.environ["MOCK_MODE"] = "1"

import app  # noqa: E402
from conftest import SAMPLES  # noqa: E402


def test_build_ui():
    demo = app.build_ui()
    assert demo is not None


def test_handle_turn_mock(tmp_path):
    app.agent.settings.output_dir = tmp_path
    out = app.handle_turn(None, "Quang hợp là gì?", [str(SAMPLES / "bai_hoc_quang_hop.pdf")],
                          "summary", "vi", "female", True, [])
    transcript, history, audio, sources, status, audio_reset, text_reset = out
    assert history[-1]["role"] == "assistant"
    assert audio and audio.endswith(".wav")
    assert "Nguồn" in sources and status.startswith("✅")
    assert audio_reset is None and text_reset == ""
