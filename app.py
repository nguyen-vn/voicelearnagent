"""Giao diện web 1 trang (Gradio) cho VoiceLearn Agent.

Chạy:  python app.py      rồi mở http://127.0.0.1:7860
"""
from __future__ import annotations

import gradio as gr

from voicelearn import GENDERS, LANGUAGES, MODES, Settings, VoiceLearnAgent
from voicelearn.documents import SUPPORTED_EXTENSIONS

settings = Settings()
agent = VoiceLearnAgent(settings)

CSS = """
#title {text-align:center}
.big-btn button, button.big-btn {font-size: 1.3rem !important; min-height: 64px}
"""


def format_sources(sources: list[dict]) -> str:
    if not sources:
        return ""
    return "**Nguồn tham khảo:**\n" + "\n".join(f"- [{s['title']}]({s['url']})" for s in sources)


def handle_turn(audio_path, text, files, mode, language, gender, use_search, history):
    """Hàm được gọi khi bấm 'Gửi' hoặc khi dừng ghi âm."""
    history = list(history or [])
    result = agent.run(
        audio_path=audio_path, text=text, files=files, mode=mode, language=language,
        gender=gender, use_search=use_search, history=history,
    )
    if result.question:
        history.append({"role": "user", "content": result.question})
    if result.answer:
        history.append({"role": "assistant", "content": result.answer})
    status = " ⚠️ ".join(result.errors) if result.errors else "✅ Xong"
    audio_out = str(result.audio_path) if result.audio_path else None
    # trả về: transcript, chatbot, audio trả lời, nguồn, trạng thái, xoá ô ghi âm & ô gõ
    return result.transcript, history, audio_out, format_sources(result.sources), status, None, ""


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="VoiceLearn Agent") as demo:
        gr.Markdown("# 🎧 VoiceLearn Agent – Trợ lý học tập bằng giọng nói", elem_id="title")
        gr.Markdown(f"`{settings.status_text()}`")

        # ----- Cấu hình -----
        with gr.Row():
            language = gr.Radio([(v["label"], k) for k, v in LANGUAGES.items()], value="vi", label="Ngôn ngữ")
            gender = gr.Radio([(v, k) for k, v in GENDERS.items()], value="female", label="Giọng đọc")
            mode = gr.Dropdown([(v, k) for k, v in MODES.items()], value="qa", label="Chế độ học")
            use_search = gr.Checkbox(value=True, label="Cho phép tìm kiếm Internet")

        # ----- Đầu vào -----
        with gr.Row():
            with gr.Column():
                audio_in = gr.Audio(sources=["microphone", "upload"], type="filepath",
                                    label="🎙️ Bấm để ghi âm câu hỏi (dừng ghi âm = tự gửi)")
                text_in = gr.Textbox(label="Hoặc gõ câu hỏi", placeholder="Ví dụ: Giải thích định luật Newton 1")
                files_in = gr.File(label="📎 Tài liệu / ảnh bài tập (PDF, PNG, JPG)",
                                   file_count="multiple", file_types=SUPPORTED_EXTENSIONS, type="filepath")
                with gr.Row():
                    send_btn = gr.Button("▶ Gửi câu hỏi", variant="primary", elem_classes="big-btn")
                    clear_btn = gr.Button("🗑 Xoá hội thoại", elem_classes="big-btn")

            # ----- Đầu ra -----
            with gr.Column():
                audio_out = gr.Audio(label="🔊 Câu trả lời bằng giọng nói", autoplay=True, interactive=False)
                transcript = gr.Textbox(label="Câu hỏi nhận diện được (Speech-to-Text)", interactive=False)
                status = gr.Markdown()
                chatbot = gr.Chatbot(label="Hội thoại", height=360)
                sources = gr.Markdown()

        inputs = [audio_in, text_in, files_in, mode, language, gender, use_search, chatbot]
        outputs = [transcript, chatbot, audio_out, sources, status, audio_in, text_in]
        send_btn.click(handle_turn, inputs, outputs)
        text_in.submit(handle_turn, inputs, outputs)
        audio_in.stop_recording(handle_turn, inputs, outputs)  # nói xong là tự gửi – tiện cho người khiếm thị
        clear_btn.click(lambda: ([], None, "", "", ""), None, [chatbot, audio_out, transcript, sources, status])
    return demo


if __name__ == "__main__":
    build_ui().launch(theme=gr.themes.Soft(), css=CSS)
