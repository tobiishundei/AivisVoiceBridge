from twitch.twitch_client import TwitchClient
from core.logger import setup_logger

from services.voice_profile_manager import VoiceProfileManager
from services.dictionary_manager import DictionaryManager
from services.speech_policy import SpeechPolicy

from speech.queue import SpeechQueue
from speech.worker import SpeechWorker

from audio.audio_engine import AudioEngine
from audio.factory import create_audio_output


class Application:

    def __init__(self, config):

        self.logger = setup_logger()

        #
        # Dictionary
        #
        self.dictionary = DictionaryManager()
        self.dictionary.load(
            config.game_dictionary
        )

        #
        # Voice Profile
        #
        self.voice_profiles = VoiceProfileManager(
            config
        )

        #
        # Speech Policy
        #
        self.policy = SpeechPolicy(
            config.speech
        )

        #
        # Queue
        #
        self.queue = SpeechQueue()

        #
        # Audio
        #
        output = create_audio_output(
            config,
            self.logger,
        )

        audio = AudioEngine(output)

        #
        # Speech Worker
        #
        self.worker = SpeechWorker(
            self.queue,
            self.logger,
            self.voice_profiles,
            config.aivis,
            audio
        )

        #
        # Twitch
        #
        self.client = TwitchClient(
            config,
            self.logger,
            self.queue,
            self.dictionary,
            self.policy,
        )

    async def start(self):

        self.logger.info("AivisVoiceBridge started")

        await self.worker.start()

        await self.client.start()

    async def stop(self):

        await self.client.stop()

        await self.worker.stop()

        self.logger.info("Application stopped")