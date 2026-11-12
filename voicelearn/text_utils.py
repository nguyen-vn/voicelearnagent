"""Text utilities: normalize questions and clean answers before they are read aloud (TTS)."""
from __future__ import annotations

import re

_MD_LINK = re.compile(r"\[([^\]]+)\]\((?:[^)]+)\)")     # [text](url) -> text
_URL = re.compile(r"https?://\S+")
_MD_SYMBOLS = re.compile(r"[*_#`>|~]+")                  # **bold**, # heading, `code`, > quote, | table
_BULLET = re.compile(r"^\s*(?:[-•+]|\d+[.)])\s+", re.MULTILINE)
_SPACES = re.compile(r"[ \t]+")
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+")


def normalize_question(text: str | None) -> str:
    """Collapse extra whitespace; return an empty string if None."""
    if not text:
        return ""
    return _SPACES.sub(" ", text.replace("\n", " ")).strip()


def clean_for_speech(text: str) -> str:
    """Strip markdown symbols / URLs so TTS doesn't read out 'asterisk, hash...'."""
    if not text:
        return ""
    text = _MD_LINK.sub(r"\1", text)
    text = _URL.sub("", text)
    text = _BULLET.sub("", text)
    text = _MD_SYMBOLS.sub("", text)
    lines = [_SPACES.sub(" ", ln).strip() for ln in text.splitlines()]
    return "\n".join(ln for ln in lines if ln)


def truncate_sentences(text: str, max_chars: int) -> str:
    """Cut the text at a sentence boundary so it doesn't exceed max_chars (saves TTS credits)."""
    if len(text) <= max_chars:
        return text
    out = ""
    for sentence in _SENTENCE_END.split(text):
        if len(out) + len(sentence) + 1 > max_chars:
            break
        out = f"{out} {sentence}".strip()
    return out or text[:max_chars]


def prepare_for_speech(text: str, max_chars: int = 1500) -> str:
    """Full cleaning pipeline: clean -> truncate."""
    return truncate_sentences(clean_for_speech(text), max_chars)