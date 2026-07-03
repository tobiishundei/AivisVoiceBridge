from dataclasses import dataclass


@dataclass(slots=True)
class VoiceProfile:

    name: str

    #
    # 話者
    #
    speaker: int = 0

    #
    # 音声パラメータ
    #
    speed: float = 1.0

    pitch: float = 0.0

    volume: float = 1.0

    enabled: bool = True