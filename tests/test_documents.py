import pytest

from conftest import SAMPLES
from voicelearn.documents import AttachmentError, load_attachment, load_attachments


def test_load_pdf_and_image():
    pdf = load_attachment(SAMPLES / "bai_hoc_quang_hop.pdf")
    img = load_attachment(SAMPLES / "bai_tap_toan.png")
    assert pdf.is_pdf and pdf.data.startswith(b"%PDF")
    assert img.mime_type == "image/png"


def test_reject_bad_extension(tmp_path):
    f = tmp_path / "notes.docx"
    f.write_bytes(b"x")
    with pytest.raises(AttachmentError):
        load_attachment(f)


def test_reject_too_large(tmp_path):
    f = tmp_path / "big.pdf"
    f.write_bytes(b"0" * (2 * 1024 * 1024))
    with pytest.raises(AttachmentError):
        load_attachment(f, max_mb=1)


def test_load_attachments_empty():
    assert load_attachments(None) == []


def test_load_attachments_accepts_path_objects():
    atts = load_attachments([SAMPLES / "bai_tap_toan.png", str(SAMPLES / "bai_hoc_quang_hop.pdf")])
    assert [a.name for a in atts] == ["bai_tap_toan.png", "bai_hoc_quang_hop.pdf"]
