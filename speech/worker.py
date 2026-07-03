import asyncio

from speech.aivis_client import AivisClient


class SpeechWorker:

    def __init__(
        self,
        queue,
        logger,
        voice_profiles,
        config,
        audio,
    ):

        self.queue = queue
        self.logger = logger

        self.voice_profiles = voice_profiles

        self._task = None
        self._running = False

        self.aivis = AivisClient(config)

        self.audio = audio

    async def start(self):

        self._running = True

        await self.aivis.start()

        await self.audio.start()

        self.task = asyncio.create_task(
            self._run()
        )

        self.logger.info("SpeechWorker started")
    
    async def stop(self):

        self._running = False

        if self.task:

            self.task.cancel()

        try:
            await self.task

        except asyncio.CancelledError:
            pass

        await self.audio.stop()

        await self.aivis.stop()

    async def _run(self):

        while self._running:

            try:

                message = await self.queue.get()

                flags = []

                if message.is_broadcaster:
                    flags.append("配信者")

                if message.is_mod:
                    flags.append("MOD")

                if message.is_vip:
                    flags.append("VIP")

                if message.is_subscriber:
                    flags.append("SUB")

                badge_text = ""

                if flags:
                    badge_text = " [" + ", ".join(flags) + "]"

                self.logger.info(
                    f"{message.user_name}{badge_text}: {message.text}"
                )

                profile = self.voice_profiles.get_profile(
                    message
                )

                self.logger.info(
                    f"VoiceProfile: {profile.name}"
                )

                wav = await self.aivis.synthesize(
                    message.text,
                    profile,
                )

                await self.audio.output(wav)

                self.queue.task_done()

            except asyncio.CancelledError:
                raise

            except Exception:
                self.logger.exception(
                    "SpeechWorker crashed"
                )