import os
import tempfile
import subprocess

from audio.audio_output import AudioOutput


class FFplayOutput(AudioOutput):

    async def start(self):

        print("FFplayOutput started")

    async def stop(self):

        print("FFplayOutput stopped")

    async def play(self, wav: bytes):

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False
        ) as f:

            f.write(wav)
            filename = f.name

        try:

            subprocess.run(
                [
                    "ffplay",
                    "-nodisp",
                    "-autoexit",
                    "-loglevel",
                    "quiet",
                    filename
                ],
                check=True
            )

        finally:

            os.remove(filename)