"""
読み上げ音声のプロファイルモデル。

ユーザー種別ごとに、使用するTTSエンジン、話者ID、
音声パラメータを切り替えるために使う。

AivisSpeech / VOICEVOX系エンジンでは、
speakerが話者・スタイルIDに対応する。
"""

from dataclasses import dataclass


@dataclass(slots=True)
class VoiceProfile:
    """
    読み上げに使う音声設定。
    """

    #
    # Profile name
    #
    name: str

    #
    # TTS engine backend
    #
    backend: str = "aivis"

    #
    # TTS engine speaker/style ID
    #
    speaker: int = 0

    #
    # Voice parameters
    #
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0

    #
    # Enable / disable this profile
    #
    enabled: bool = True