"""VoiceLearn Agent – trợ lý học tập bằng giọng nói (STT → Gemini → TTS)."""
from .config import GENDERS, LANGUAGES, MODES, Settings
from .pipeline import TurnResult, VoiceLearnAgent

__all__ = ["Settings", "VoiceLearnAgent", "TurnResult", "LANGUAGES", "GENDERS", "MODES"]
__version__ = "0.1.0"