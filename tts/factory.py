"""
設定に応じてTTSエンジンを生成する。

音声プロファイルで使用されているバックエンドを調べ、
AivisSpeech Engine、VOICEVOX Engineを必要に応じて生成する。
"""

from tts.aivis_engine import AivisEngine
from tts.manager import TtsEngineManager
from tts.voicevox_engine import VoicevoxEngine


SUPPORTED_BACKENDS = {
    "aivis",
    "voicevox",
}


def get_required_tts_backends(
    config,
) -> set[str]:
    """
    有効な音声プロファイルで使用される
    TTSバックエンドを取得する。

    defaultプロファイルは、他プロファイルが無効な場合の
    フォールバックにも使われるため必ず対象に含める。
    """
    required_backends: set[str] = set()

    default_profile = (
        config.voice_profiles.get("default")
    )

    if default_profile is None:
        raise RuntimeError(
            "default voice profile is required"
        )

    required_backends.add(
        default_profile.backend
    )

    for name, profile in (
        config.voice_profiles.items()
    ):
        if name == "default":
            continue

        if profile.enabled:
            required_backends.add(
                profile.backend
            )

    unknown_backends = (
        required_backends
        - SUPPORTED_BACKENDS
    )

    if unknown_backends:
        backend_names = ", ".join(
            sorted(unknown_backends)
        )

        raise RuntimeError(
            "Unknown TTS backend: "
            f"{backend_names}"
        )

    return required_backends


def create_tts_engine_manager(
    config,
) -> TtsEngineManager:
    """
    必要なTTSエンジンを生成し、
    TtsEngineManagerとして返す。
    """
    required_backends = (
        get_required_tts_backends(config)
    )

    engines = {}

    if "aivis" in required_backends:
        engines["aivis"] = AivisEngine(
            config.aivis
        )

    if "voicevox" in required_backends:
        engines["voicevox"] = (
            VoicevoxEngine(
                config.voicevox
            )
        )

    return TtsEngineManager(
        engines
    )

def create_tts_engine(
    config,
):
    """
    従来コードとの互換性のため、
    config.tts.backendで指定された
    単一のTTSエンジンを生成する。

    通常の読み上げ処理では
    create_tts_engine_manager()を使用する。
    """
    backend = config.tts.backend

    if backend == "aivis":
        return AivisEngine(
            config.aivis
        )

    if backend == "voicevox":
        return VoicevoxEngine(
            config.voicevox
        )

    raise RuntimeError(
        f"Unknown TTS backend: {backend}"
    )