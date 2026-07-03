"""
OBS 初回設定用の音声テストコマンド。

AivisVoiceBridge の PipeWire 音声ノードを OBS 側で選択しやすくするため、
通常のコメント読み上げより長めのテスト音声を再生する。
"""

from audio.audio_engine import AudioEngine
from audio.factory import create_audio_output
from core.logger import setup_logger
from tts.factory import create_tts_engine


AUDIO_TEST_TEXT = (
    "AivisVoiceBridgeの音声出力テストです。"
    "OBS StudioのApplication Audio Capture、PipeWireで、"
    "アプリケーション一覧からAivisVoiceBridgeを選択してください。"
    "この音声は初回設定のために少し長めに再生されています。"
    "音声メーターが反応していれば設定は成功です。"
)


async def run_audio_test(config):
    """
    音声出力テストを実行する。

    Twitchには接続せず、TTSエンジンと音声出力のみを使う。
    """

    logger = setup_logger()

    logger.info(
        "AivisVoiceBridge audio test started"
    )

    tts = create_tts_engine(
        config
    )

    output = create_audio_output(
        config,
        logger,
    )

    audio = AudioEngine(output)

    profile = config.voice_profiles["default"]

    try:
        await tts.start()
        await audio.start()

        wav = await tts.synthesize(
            AUDIO_TEST_TEXT,
            profile,
        )

        await audio.output(wav)

    finally:
        await audio.stop()
        await tts.stop()

    logger.info(
        "AivisVoiceBridge audio test finished"
    )