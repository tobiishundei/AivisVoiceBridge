import asyncio
import os
import shutil
import subprocess
import tempfile

from audio.audio_output import AudioOutput


class PipeWireOutput(AudioOutput):

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
        if self.logger:
            self.logger.info(message)
        else:
            print(message)

    def _error(self, message: str):
        if self.logger:
            self.logger.error(message)
        else:
            print(message)

    async def start(self):
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
        self._info(
            "PipeWireOutput stopped"
        )

    async def output(self, wav: bytes):
        if not self._available:
            raise RuntimeError(
                "PipeWireOutput is not started"
            )

        filename = None

        try:
            with tempfile.NamedTemporaryFile(
                suffix=".wav",
                delete=False
            ) as f:
                f.write(wav)
                filename = f.name

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

        finally:
            if filename and os.path.exists(filename):
                os.remove(filename)