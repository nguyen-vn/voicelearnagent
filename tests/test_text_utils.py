from voicelearn.text_utils import clean_for_speech, normalize_question, prepare_for_speech, truncate_sentences


def test_normalize_question():
    assert normalize_question("  Quang   hợp\n là gì? ") == "Quang hợp là gì?"
    assert normalize_question(None) == ""


def test_clean_for_speech_removes_markdown_and_urls():
    raw = "# Tiêu đề\n**Quang hợp** là `quá trình`.\n- Ý một\n1. Ý hai\nXem [Wiki](https://wiki.org) https://x.y"
    out = clean_for_speech(raw)
    for sym in ["#", "*", "`", "http", "- ", "1."]:
        assert sym not in out
    assert "Quang hợp là quá trình." in out
    assert "Xem Wiki" in out


def test_truncate_keeps_whole_sentences():
    text = "Câu một. Câu hai dài hơn. Câu ba."
    assert truncate_sentences(text, 20) == "Câu một."
    assert truncate_sentences(text, 1000) == text


def test_prepare_for_speech_limit():
    assert len(prepare_for_speech("Một câu. " * 500, 200)) <= 200
