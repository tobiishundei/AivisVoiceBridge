"""
設定に応じて TTS エンジンを生成する。

AivisSpeech Engine、VOICEVOX Engine などの切り替えをここで行う。
"""

from tts.aivis_engine import AivisEngine
from tts.voicevox_engine import VoicevoxEngine


def create_tts_engine(config):
    """
    config.tts.backend に応じた TTSエンジンを生成する。
    """

    backend = config.tts.backend

    if backend == "aivis":
        return AivisEngine(
            config.aivis
        )

    if backend == "voicevox":
        return VoicevoxEngine(
            config.voicevox
        )

    raise RuntimeError(
        f"Unknown TTS backend: {backend}"
    )