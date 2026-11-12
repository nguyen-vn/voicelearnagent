"""Liệt kê các giọng ElevenLabs mà tài khoản của bạn dùng được (để điền VOICE_*_ID trong .env).

Chạy: python scripts/list_voices.py [từ_khoá]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voicelearn.config import Settings  # noqa: E402


def main():
    settings = Settings()
    if not settings.elevenlabs_api_key:
        sys.exit("Chưa có ELEVENLABS_API_KEY trong .env")
    from elevenlabs.client import ElevenLabs

    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    keyword = sys.argv[1] if len(sys.argv) > 1 else None
    resp = client.voices.search(search=keyword, page_size=100)
    print(f"{'VOICE_ID':<24} {'NAME':<28} {'GENDER':<8} ACCENT / LANGUAGE")
    for v in resp.voices:
        labels = v.labels or {}
        print(f"{v.voice_id:<24} {v.name[:27]:<28} {labels.get('gender', '-'):<8} "
              f"{labels.get('accent', '-')} / {labels.get('language', '-')}")


if __name__ == "__main__":
    main()
