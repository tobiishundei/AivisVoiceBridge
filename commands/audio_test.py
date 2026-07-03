from core.logger import setup_logger

from audio.audio_engine import AudioEngine
from audio.factory import create_audio_output
from speech.aivis_client import AivisClient


async def run_audio_test(config):
    logger = setup_logger()

    logger.info(
        "AivisVoiceBridge audio test started"
    )

    aivis = AivisClient(config.aivis)

    output = create_audio_output(
        config,
        logger,
    )

    audio = AudioEngine(output)

    profile = config.voice_profiles["default"]

    text = (
        "AivisVoiceBridgeの音声出力テストです。"
        "OBS StudioのApplication Audio Capture、PipeWireで、"
        "アプリケーション一覧からAivisVoiceBridgeを選択してください。"
        "この音声は初回設定のために少し長めに再生されています。"
        "音声メーターが反応していれば設定は成功です。"
    )

    try:
        await aivis.start()
        await audio.start()

        wav = await aivis.synthesize(
            text,
            profile,
        )

        await audio.output(wav)

    finally:
        await audio.stop()
        await aivis.stop()

    logger.info(
        "AivisVoiceBridge audio test finished"
    )