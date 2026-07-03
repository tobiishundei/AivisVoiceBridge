"""
読み上げ処理をバックグラウンドで実行するワーカー。

SpeechQueue から ChatMessage を取り出し、
VoiceProfile を選択して TTS 音声を生成し、AudioEngine へ渡す。
"""

import asyncio


class SpeechWorker:
    """
    チャットメッセージを順番に読み上げる非同期ワーカー。
    """

    def __init__(
        self,
        queue,
        logger,
        voice_profiles,
        tts,
        audio,
    ):
        self.queue = queue
        self.logger = logger
        self.voice_profiles = voice_profiles
        self.tts = tts
        self.audio = audio

        self._task = None
        self._running = False

    async def start(self):
        """
        TTSエンジンと音声出力を開始し、読み上げワーカーを起動する。
        """

        if self._running:
            return

        self._running = True

        await self.tts.start()
        await self.audio.start()

        self._task = asyncio.create_task(
            self._run()
        )

        self.logger.info(
            "SpeechWorker started"
        )

    async def stop(self):
        """
        読み上げワーカーを停止し、TTSエンジンと音声出力を終了する。
        """

        self._running = False

        if self._task:
            self._task.cancel()

            try:
                await self._task

            except asyncio.CancelledError:
                pass

            self._task = None

        await self.audio.stop()
        await self.tts.stop()

    async def _run(self):
        """
        キューからメッセージを取り出して読み上げ続ける。
        """

        while self._running:
            message = None

            try:
                message = await self.queue.get()

                await self._handle_message(message)

            except asyncio.CancelledError:
                raise

            except Exception:
                self.logger.exception(
                    "SpeechWorker crashed"
                )

            finally:
                if message is not None:
                    self.queue.task_done()

    async def _handle_message(self, message):
        """
        1件のチャットメッセージを音声合成して出力する。
        """

        self._log_message(message)

        profile = self.voice_profiles.get_profile(
            message
        )

        self.logger.info(
            f"VoiceProfile: {profile.name}"
        )

        wav = await self.tts.synthesize(
            message.text,
            profile,
        )

        await self.audio.output(wav)

    def _log_message(self, message):
        """
        読み上げ対象メッセージをログに出力する。
        """

        badge_text = self._build_badge_text(message)

        self.logger.info(
            f"{message.user_name}{badge_text}: {message.text}"
        )

    def _build_badge_text(self, message) -> str:
        """
        ユーザー属性をログ表示用の文字列に変換する。
        """

        flags = []

        if message.is_broadcaster:
            flags.append("配信者")

        if message.is_mod:
            flags.append("MOD")

        if message.is_vip:
            flags.append("VIP")

        if message.is_subscriber:
            flags.append("SUB")

        if not flags:
            return ""

        return " [" + ", ".join(flags) + "]"