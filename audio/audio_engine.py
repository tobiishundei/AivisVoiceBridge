"""
音声出力を扱う上位レイヤー。

SpeechWorker は具体的な出力方法を知らず、
AudioEngine を通して音声を出力する。
"""

from audio.audio_output import AudioOutput


class AudioEngine:
    """
    音声出力バックエンドをラップするクラス。
    """

    def __init__(self, output: AudioOutput):
        self.output_backend = output

    async def start(self):
        """
        音声出力を開始する。
        """

        await self.output_backend.start()

    async def stop(self):
        """
        音声出力を停止する。
        """

        await self.output_backend.stop()

    async def output(self, wav: bytes):
        """
        WAV形式の音声データを出力する。
        """

        await self.output_backend.output(wav)