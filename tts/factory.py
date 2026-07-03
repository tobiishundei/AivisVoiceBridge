"""
設定に応じて TTS エンジンを生成する。

現時点では AivisSpeech Engine を使用する。
VOICEVOX Engine 対応時に backend 切り替えを追加する。
"""

from tts.aivis_engine import AivisEngine


def create_tts_engine(config):
    """
    TTSエンジンを生成する。
    """

    return AivisEngine(
        config.aivis
    )