"""
AivisVoiceBridge アプリケーション本体の組み立てを行う。

このクラスは、各コンポーネントを生成して接続する。
実際の処理は TwitchClient、SpeechWorker、各 service に委譲する。
"""

from audio.audio_engine import AudioEngine
from audio.factory import create_audio_output
from core.logger import setup_logger
from services.dictionary_manager import DictionaryManager
from services.speech_policy import SpeechPolicy
from services.voice_profile_manager import VoiceProfileManager
from speech.queue import SpeechQueue
from speech.worker import SpeechWorker
from twitch.twitch_client import TwitchClient


class Application:
    """
    AivisVoiceBridge の主要コンポーネントを束ねるクラス。
    """

    def __init__(self, config):
        self.config = config
        self.logger = setup_logger()

        self.dictionary = self._create_dictionary()
        self.voice_profiles = VoiceProfileManager(config)
        self.policy = SpeechPolicy(config.speech)
        self.queue = SpeechQueue()

        self.audio = self._create_audio_engine()

        self.worker = SpeechWorker(
            self.queue,
            self.logger,
            self.voice_profiles,
            config.aivis,
            self.audio,
        )

        self.client = TwitchClient(
            config,
            self.logger,
            self.queue,
            self.dictionary,
            self.policy,
        )

    def _create_dictionary(self):
        """
        設定に応じた辞書を読み込む。
        """

        dictionary = DictionaryManager()
        dictionary.load(
            self.config.game_dictionary
        )

        return dictionary

    def _create_audio_engine(self):
        """
        設定に応じた音声出力バックエンドを生成する。
        """

        output = create_audio_output(
            self.config,
            self.logger,
        )

        return AudioEngine(output)

    async def start(self):
        """
        アプリケーションを起動する。

        ここでは各コンポーネントの開始のみ行う。
        常駐のための待機処理は main.py 側で行う。
        """

        self.logger.info("AivisVoiceBridge started")

        await self.worker.start()
        await self.client.start()

    async def stop(self):
        """
        アプリケーションを停止する。
        """

        await self.client.stop()
        await self.worker.stop()

        self.logger.info("Application stopped")