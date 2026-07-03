"""
AivisSpeech Engine 用の TTS エンジン。

AivisSpeech Engine は VOICEVOX 互換に近い API を持つため、
/audio_query でクエリを生成し、/synthesis で WAV 音声を生成する。
"""

import aiohttp

from tts.tts_engine import TtsEngine


class AivisEngine(TtsEngine):
    """
    AivisSpeech Engine の音声合成APIを扱う TTS エンジン。
    """

    def __init__(self, config):
        self.base_url = (
            f"http://{config.host}:{config.port}"
        )

        self.session = None

    async def start(self):
        """
        HTTPセッションを開始する。
        """

        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def stop(self):
        """
        HTTPセッションを終了する。
        """

        if self.session is not None:
            await self.session.close()
            self.session = None

    async def synthesize(
        self,
        text: str,
        profile,
    ) -> bytes:
        """
        テキストと VoiceProfile から WAV 音声を生成する。
        """

        self._ensure_started()

        query = await self._create_audio_query(
            text,
            profile,
        )

        self._apply_voice_profile(
            query,
            profile,
        )

        return await self._synthesize_wav(
            query,
            profile,
        )

    def _ensure_started(self):
        """
        start() が呼ばれていることを確認する。
        """

        if self.session is None:
            raise RuntimeError(
                "AivisEngine is not started"
            )

    async def _create_audio_query(
        self,
        text: str,
        profile,
    ) -> dict:
        """
        /audio_query を呼び出して音声合成用クエリを生成する。
        """

        async with self.session.post(
            f"{self.base_url}/audio_query",
            params={
                "text": text,
                "speaker": profile.speaker,
            },
        ) as response:
            response.raise_for_status()

            return await response.json()

    def _apply_voice_profile(
        self,
        query: dict,
        profile,
    ):
        """
        VoiceProfile の音声パラメータを audio_query に反映する。
        """

        query["speedScale"] = profile.speed
        query["pitchScale"] = profile.pitch
        query["volumeScale"] = profile.volume

    async def _synthesize_wav(
        self,
        query: dict,
        profile,
    ) -> bytes:
        """
        /synthesis を呼び出して WAV 音声を生成する。
        """

        async with self.session.post(
            f"{self.base_url}/synthesis",
            params={
                "speaker": profile.speaker,
            },
            json=query,
        ) as response:
            response.raise_for_status()

            return await response.read()