"""
複数のTTSエンジンを管理する。

VoiceProfile.backendに応じて、
AivisSpeech EngineまたはVOICEVOX Engineへ
音声合成処理を振り分ける。
"""

import asyncio

from tts.tts_engine import TtsEngine


class TtsEngineManager:
    """
    複数のTTSエンジンをまとめて管理する。
    """

    def __init__(
        self,
        engines: dict[str, TtsEngine],
    ):
        self.engines = engines
        self._started = False

    async def start(self):
        """
        登録されているすべてのTTSエンジンを開始する。
        """
        if self._started:
            return

        started_engines: list[TtsEngine] = []

        try:
            for engine in self.engines.values():
                await engine.start()
                started_engines.append(engine)

        except Exception:
            await asyncio.gather(
                *(
                    engine.stop()
                    for engine in reversed(
                        started_engines
                    )
                ),
                return_exceptions=True,
            )

            raise

        self._started = True

    async def stop(self):
        """
        登録されているすべてのTTSエンジンを停止する。
        """
        if not self._started:
            return

        await asyncio.gather(
            *(
                engine.stop()
                for engine in self.engines.values()
            ),
            return_exceptions=True,
        )

        self._started = False

    async def synthesize(
        self,
        text: str,
        profile,
    ) -> bytes:
        """
        VoiceProfile.backendに対応する
        TTSエンジンで音声を合成する。
        """
        if not self._started:
            raise RuntimeError(
                "TtsEngineManager is not started"
            )

        backend = profile.backend

        engine = self.engines.get(
            backend
        )

        if engine is None:
            raise RuntimeError(
                "TTS engine is not available: "
                f"{backend}"
            )

        return await engine.synthesize(
            text,
            profile,
        )