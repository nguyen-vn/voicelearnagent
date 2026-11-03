"""Tiện ích xử lý văn bản: chuẩn hoá câu hỏi và làm sạch câu trả lời trước khi đọc (TTS)."""
from __future__ import annotations

import re

_MD_LINK = re.compile(r"\[([^\]]+)\]\((?:[^)]+)\)")     # [text](url) -> text
_URL = re.compile(r"https?://\S+")
_MD_SYMBOLS = re.compile(r"[*_#`>|~]+")                  # **bold**, # heading, `code`, > quote, | table
_BULLET = re.compile(r"^\s*(?:[-•+]|\d+[.)])\s+", re.MULTILINE)
_SPACES = re.compile(r"[ \t]+")
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


def normalize_question(text: str | None) -> str:
    """Bỏ khoảng trắng thừa; trả về chuỗi rỗng nếu None."""
    if not text:
        return ""
    return _SPACES.sub(" ", text.replace("\n", " ")).strip()


def clean_for_speech(text: str) -> str:
    """Loại bỏ ký hiệu markdown / URL để TTS không đọc 'dấu sao, thăng...'."""
    if not text:
        return ""
    text = _MD_LINK.sub(r"\1", text)
    text = _URL.sub("", text)
    text = _BULLET.sub("", text)
    text = _MD_SYMBOLS.sub("", text)
    lines = [_SPACES.sub(" ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def truncate_sentences(text: str, max_chars: int) -> str:
    """Cắt văn bản ở ranh giới câu để không vượt quá max_chars (tiết kiệm credit TTS)."""
    if len(text) <= max_chars:
        return text
    out = ""
    for sentence in _SENTENCE_END.split(text):
        if len(out) + len(sentence) + 1 > max_chars:
            break
        out = f"{out} {sentence}".strip()
    return out or text[:max_chars]


def prepare_for_speech(text: str, max_chars: int = 1500) -> str:
    """Pipeline làm sạch hoàn chỉnh: clean -> truncate."""
    return truncate_sentences(clean_for_speech(text), max_chars)
