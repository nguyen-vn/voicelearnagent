"""Read attachments (PDF / image) into bytes + mime type to send directly to Gemini.

Gemini can read PDFs and images directly (multimodal), so no OCR or page splitting is needed.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

MIME_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
SUPPORTED_EXTENSIONS = list(MIME_TYPES)


class AttachmentError(ValueError):
    """Invalid file (wrong format, too large, or does not exist)."""


@dataclass
class Attachment:
    name: str
    mime_type: str
    data: bytes

    @property
    def is_pdf(self) -> bool:
        return self.mime_type == "application/pdf"

    @property
    def size_kb(self) -> float:
        return len(self.data) / 1024


def load_attachment(path: str | Path, max_mb: int = 20) -> Attachment:
    path = Path(path)
    if not path.exists():
        raise AttachmentError(f"Không tìm thấy file: {path.name}")
    mime = MIME_TYPES.get(path.suffix.lower())
    if mime is None:
        raise AttachmentError(
            f"Định dạng {path.suffix} chưa hỗ trợ. Hãy dùng: {', '.join(SUPPORTED_EXTENSIONS)}"
        )
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_mb:
        raise AttachmentError(f"File {path.name} nặng {size_mb:.1f} MB, vượt giới hạn {max_mb} MB.")
    return Attachment(name=path.name, mime_type=mime, data=path.read_bytes())


def load_attachments(paths: list | None, max_mb: int = 20) -> list[Attachment]:
    """Take a list of paths (or Gradio file objects) -> list of Attachment."""
    result = []
    for p in paths or []:
        if not isinstance(p, (str, Path)):
            p = getattr(p, "name", p)  # older Gradio versions return file objects with a .name attribute
        result.append(load_attachment(p, max_mb=max_mb))
    return result