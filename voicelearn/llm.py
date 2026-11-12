"""The agent's brain: calls Gemini (optionally with Google Search) to answer questions / read files.

Two classes share the SAME `ask(...)` interface:
- GeminiTutor : calls the real API (google-genai SDK)
- MockTutor   : returns simulated answers, no API key needed (for learning & testing)
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .documents import Attachment


class LLMError(RuntimeError):
    """Error when calling the LLM (wrong key, quota exceeded, network...)."""


@dataclass
class LLMAnswer:
    text: str
    sources: list[dict] = field(default_factory=list)  # [{"title": ..., "url": ...}]


# history uses Gradio's "messages" format: [{"role": "user"|"assistant", "content": str}]
History = list[dict]


class GeminiTutor:
    def __init__(self, api_key: str, model: str = "gemini-3.8-flash", client=None):
        if client is None:
            from google import genai  # lazy import so mock mode doesn't need the SDK

            client = genai.Client(api_key=api_key)
        self.client = client
        self.model = model

    # ---------- build the request ----------
    @staticmethod
    def build_contents(question: str, history: History | None, attachments: list[Attachment] | None):
        from google.genai import types

        contents = []
        for msg in history or []:
            text = msg.get("content")
            if not isinstance(text, str) or not text:
                continue  # skip non-text messages (audio, files...)
            role = "model" if msg.get("role") == "assistant" else "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))

        parts = [types.Part.from_bytes(data=a.data, mime_type=a.mime_type) for a in attachments or []]
        parts.append(types.Part.from_text(text=question))
        contents.append(types.Content(role="user", parts=parts))
        return contents

    @staticmethod
    def build_config(system_prompt: str, use_search: bool):
        from google.genai import types

        tools = [types.Tool(google_search=types.GoogleSearch())] if use_search else None
        return types.GenerateContentConfig(system_instruction=system_prompt, tools=tools, temperature=0.4)

    @staticmethod
    def extract_sources(response) -> list[dict]:
        """Extract the list of web sources from grounding metadata (when Google Search is enabled)."""
        sources, seen = [], set()
        try:
            chunks = response.candidates[0].grounding_metadata.grounding_chunks or []
        except (AttributeError, IndexError, TypeError):
            return sources
        for chunk in chunks:
            web = getattr(chunk, "web", None)
            url = getattr(web, "uri", None)
            if url and url not in seen:
                seen.add(url)
                sources.append({"title": getattr(web, "title", None) or url, "url": url})
        return sources

    # ---------- call the API ----------
    def ask(
        self,
        question: str,
        *,
        system_prompt: str,
        history: History | None = None,
        attachments: list[Attachment] | None = None,
        use_search: bool = False,
    ) -> LLMAnswer:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=self.build_contents(question, history, attachments),
                config=self.build_config(system_prompt, use_search),
            )
        except Exception as exc:  # noqa: BLE001 - collapse all SDK errors into one type
            raise LLMError(f"Gemini lỗi: {exc}") from exc
        text = (response.text or "").strip()
        if not text:
            raise LLMError("Gemini không trả về nội dung (có thể bị chặn bởi bộ lọc an toàn).")
        return LLMAnswer(text=text, sources=self.extract_sources(response))


class MockTutor:
    """Simulated answers, for test-running the whole pipeline without spending API calls."""

    def __init__(self):
        self.calls: list[dict] = []  # record requests for testing/inspection

    def ask(self, question, *, system_prompt, history=None, attachments=None, use_search=False) -> LLMAnswer:
        self.calls.append(
            dict(question=question, system_prompt=system_prompt, history=history,
                 attachments=attachments, use_search=use_search)
        )
        vi = "Vietnamese" in system_prompt
        files = ", ".join(a.name for a in attachments or []) or ("không có" if vi else "none")
        if vi:
            text = (f"Đây là câu trả lời mẫu ở chế độ mock. Bạn hỏi: {question} "
                    f"File đính kèm: {files}. Khi có GEMINI_API_KEY, Gemini sẽ trả lời thật.")
        else:
            text = (f"This is a mock answer. You asked: {question} "
                    f"Attachments: {files}. Add GEMINI_API_KEY to get real answers.")
        sources = [{"title": "Mock source", "url": "https://example.com"}] if use_search else []
        return LLMAnswer(text=text, sources=sources)