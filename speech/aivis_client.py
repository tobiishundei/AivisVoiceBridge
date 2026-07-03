import aiohttp


class AivisClient:

    def __init__(self, config):

        self.base_url = (
            f"http://{config.host}:{config.port}"
        )

        self.session = None

    async def start(self):

        if self.session is None:

            self.session = aiohttp.ClientSession()

    async def stop(self):

        if self.session is not None:

            await self.session.close()

            self.session = None

    async def synthesize(
        self,
        text: str,
        profile,
    ) -> bytes:

        #
        # AudioQuery生成
        #
        async with self.session.post(
            f"{self.base_url}/audio_query",
            params={
                "text": text,
                "speaker": profile.speaker,
            },
        ) as response:

            query = await response.json()

        #
        # パラメータ変更
        #
        query["speedScale"] = profile.speed
        query["pitchScale"] = profile.pitch
        query["volumeScale"] = profile.volume

        #
        # 音声合成
        #
        async with self.session.post(
            f"{self.base_url}/synthesis",
            params={
                "speaker": profile.speaker,
            },
            json=query,
        ) as response:

            wav = await response.read()

        return wav