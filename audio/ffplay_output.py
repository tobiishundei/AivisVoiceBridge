"""
ffplay向けの音声出力バックエンド。

主にPipeWireを使わない環境や、簡易テスト用のフォールバックとして使う。
OBSでアプリ別キャプチャを行う場合は PipeWireOutput の利用を推奨する。
"""

import asyncio
import os
import shutil
import subprocess
import tempfile

from audio.audio_output import AudioOutput


class FFplayOutput(AudioOutput):
    """
    `ffplay` を使ってWAV音声を再生するバックエンド。
    """

    def __init__(self, logger=None):
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
        `ffplay` が利用可能か確認する。
        """

        path = shutil.which("ffplay")

        if not path:
            raise RuntimeError(
                "ffplay が見つかりません。"
                " ffmpeg パッケージをインストールしてください。"
            )

        self._available = True

        self._info(
            f"FFplayOutput started: {path}"
        )

    async def stop(self):
        """
        ffplay出力を停止する。

        現在の実装では `ffplay` は再生ごとに終了するため、
        ここではログ出力のみ行う。
        """

        self._info(
            "FFplayOutput stopped"
        )

    async def output(self, wav: bytes):
        """
        WAV音声を一時ファイルに保存し、`ffplay` で再生する。
        """

        if not self._available:
            raise RuntimeError(
                "FFplayOutput is not started"
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
        `ffplay` を起動して指定ファイルを再生する。
        """

        proc = subprocess.Popen(
            [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "error",
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
                "ffplay failed: "
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