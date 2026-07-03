from audio.ffplay_output import FFplayOutput
from audio.pipewire_output import PipeWireOutput


def create_audio_output(config, logger=None):
    audio = config.audio
    backend = audio.backend

    if backend == "pipewire":
        return PipeWireOutput(
            app_name=audio.app_name,
            media_role=audio.media_role,
            logger=logger,
        )

    if backend == "ffplay":
        return FFplayOutput()

    raise RuntimeError(
        f"Unknown audio backend: {backend}"
    )