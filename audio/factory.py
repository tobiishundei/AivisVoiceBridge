"""
設定に応じて音声出力バックエンドを生成する。
"""

from audio.ffplay_output import FFplayOutput
from audio.persistent_output import PersistentAudioOutput
from audio.pipewire_output import PipeWireOutput


def create_audio_output(config, logger=None):
    """
    config.audio.backend に応じた AudioOutput を生成する。
    """

    audio = config.audio
    backend = audio.backend

    if backend == "pipewire":
        return PipeWireOutput(
            app_name=audio.app_name,
            media_role=audio.media_role,
            logger=logger,
        )

    if backend == "ffplay":
        return FFplayOutput(
            logger=logger,
        )

    if backend == "persistent":
        return PersistentAudioOutput(
            app_name=audio.app_name,
            logger=logger,
        )

    raise RuntimeError(
        f"Unknown audio backend: {backend}"
    )
