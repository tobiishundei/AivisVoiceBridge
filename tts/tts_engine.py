"""
TTSエンジンの共通インターフェース。

AivisSpeech Engine、VOICEVOX Engine など、
テキストからWAV音声を生成するエンジンはこのインターフェースに揃える。
"""

from abc import ABC
from abc import abstractmethod


class TtsEngine(ABC):
    """
    TTSエンジンの基底クラス。
    """

    async def start(self):
        """
        TTSエンジンを開始する。

        HTTPセッションの作成など、必要な初期化を行う。
        """

        pass

    async def stop(self):
        """
        TTSエンジンを停止する。

        HTTPセッションの終了など、必要な終了処理を行う。
        """

        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        profile,
    ) -> bytes:
        """
        テキストと VoiceProfile から WAV 音声を生成する。
        """

        pass