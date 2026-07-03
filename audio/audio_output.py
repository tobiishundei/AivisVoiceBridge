"""
音声出力バックエンドの共通インターフェース。

PipeWire、ffplay、将来の別バックエンドはこのクラスを継承する。
"""

from abc import ABC
from abc import abstractmethod


class AudioOutput(ABC):
    """
    音声出力バックエンドの基底クラス。
    """

    async def start(self):
        """
        音声出力バックエンドを開始する。

        必要な初期化がないバックエンドでは何もしない。
        """

        pass

    async def stop(self):
        """
        音声出力バックエンドを停止する。

        必要な終了処理がないバックエンドでは何もしない。
        """

        pass

    @abstractmethod
    async def output(self, wav: bytes):
        """
        WAV形式の音声データを出力する。
        """

        pass