from audio.audio_output import AudioOutput


class AudioEngine:

    def __init__(self, output: AudioOutput):
        self.output_backend = output

    async def start(self):
        await self.output_backend.start()

    async def stop(self):
        await self.output_backend.stop()

    async def output(self, wav: bytes):
        await self.output_backend.output(wav)