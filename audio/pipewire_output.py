"""
PipeWire向けの音声出力バックエンド。

AivisVoiceBridgeでは、Linux / PipeWire環境で `pw-play` を使ってWAVを再生する。
OBS Studioでは obs-pipewire-audio-capture プラグインを使うことで、
application.name に指定した名前のアプリ音声として個別キャプチャできる。
"""

import asyncio
import os
import shutil
import subprocess
import tempfile

from audio.audio_output import AudioOutput


class PipeWireOutput(AudioOutput):
    """
    `pw-play` を使ってWAV音声をPipeWireへ出力するバックエンド。
    """

    def __init__(
        self,
        app_name: str,
        media_role: str,
        logger=None,
    ):
        self.app_name = app_name
        self.media_role = media_role
        self.logger = logger
        self._available = False

    def _info(self, message: str):
        """
        logger があれば info として出力し、なければ print にフォールバックする。
        """

        if self.logger:
            self.logger.info(message)
        else:
            print(message)

    def _error(self, message: str):
        """
        logger があれば error として出力し、なければ print にフォールバックする。
        """

        if self.logger:
            self.logger.error(message)
        else:
            print(message)

    async def start(self):
        """
        `pw-play` が利用可能か確認する。
        """

        path = shutil.which("pw-play")

        if not path:
            raise RuntimeError(
                "pw-play が見つかりません。"
                " PipeWire の pw-play コマンドをインストールしてください。"
            )

        self._available = True

        self._info(
            f"PipeWireOutput started: {path}"
        )

    async def stop(self):
        """
        PipeWire出力を停止する。

        現在の実装では `pw-play` は再生ごとに終了するため、
        ここではログ出力のみ行う。
        """

        self._info(
            "PipeWireOutput stopped"
        )

    async def output(self, wav: bytes):
        """
        WAV音声を一時ファイルに保存し、`pw-play` で再生する。
        """

        if not self._available:
            raise RuntimeError(
                "PipeWireOutput is not started"
            )

        filename = None

        try:
            filename = self._write_temp_wav(wav)

            await self._play_file(filename)

        finally:
            self._remove_temp_file(filename)

    def _write_temp_wav(self, wav: bytes) -> str:
        """
        WAVデータを一時ファイルとして保存し、ファイルパスを返す。
        """

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as f:
            f.write(wav)
            return f.name

    async def _play_file(self, filename: str):
        """
        `pw-play` を起動して指定ファイルを再生する。
        """

        proc = subprocess.Popen(
            [
                "pw-play",

                "-P", f"node.name={self.app_name}",
                "-P", f"node.description={self.app_name}",

                "-P", f"application.name={self.app_name}",
                "-P", f"application.process.binary={self.app_name}",

                "-P", f"media.name={self.app_name}",
                "-P", f"media.role={self.media_role}",

                filename,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        _, stderr = await asyncio.to_thread(
            proc.communicate
        )

        if proc.returncode != 0:
            message = (
                "pw-play failed: "
                f"{stderr.strip()}"
            )

            self._error(message)

            raise RuntimeError(message)

    def _remove_temp_file(self, filename: str | None):
        """
        再生用の一時WAVファイルを削除する。
        """

        if filename and os.path.exists(filename):
            os.remove(filename)