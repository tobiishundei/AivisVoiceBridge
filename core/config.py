"""
AivisVoiceBridge の設定読み込みを行う。

settings/config.json を読み込み、アプリ全体で使う Config オブジェクトへ変換する。
秘密情報を含む config.json は Git 管理しない。
"""

import json
from dataclasses import dataclass
from pathlib import Path

from twitchAPI.type import AuthScope

from models.voice_profile import VoiceProfile


CONFIG_PATH = Path("settings") / "config.json"


@dataclass
class AivisConfig:
    """
    AivisSpeech Engine への接続設定。
    """

    host: str
    port: int

@dataclass
class VoicevoxConfig:
    """
    VOICEVOX Engine への接続設定。
    """

    host: str
    port: int

@dataclass
class SpeechConfig:
    """
    読み上げ可否を判定するための設定。
    """

    max_length: int
    cooldown: float
    skip_url_only: bool
    skip_empty: bool


@dataclass
class AudioConfig:
    """
    音声出力バックエンドの設定。
    """

    backend: str
    app_name: str
    media_role: str

@dataclass
class TtsConfig:
    """
    使用する TTS エンジンの設定。
    """

    backend: str

@dataclass
class Config:
    """
    アプリケーション全体の設定。
    """

    client_id: str
    client_secret: str
    channel: str
    redirect_uri: str
    token_file: str
    scopes: list[AuthScope]

    game_dictionary: str

    tts: TtsConfig
    aivis: AivisConfig
    voicevox: VoicevoxConfig
    speech: SpeechConfig
    audio: AudioConfig
    voice_profiles: dict[str, VoiceProfile]


_SCOPE_MAP = {
    "CHAT_READ": AuthScope.CHAT_READ,
    "CHAT_EDIT": AuthScope.CHAT_EDIT,
    "USER_READ_CHAT": AuthScope.USER_READ_CHAT,
    "USER_BOT": AuthScope.USER_BOT,
    "CHANNEL_BOT": AuthScope.CHANNEL_BOT,
}


def load_config() -> Config:
    """
    config.json を読み込み、Config オブジェクトを返す。
    """

    data = _load_json(CONFIG_PATH)

    return Config(
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        channel=data["channel"],
        redirect_uri=data["redirect_uri"],
        token_file=data["token_file"],
        scopes=_load_scopes(data),
        game_dictionary=data["game_dictionary"],
        tts=_load_tts_config(data),
        aivis=_load_aivis_config(data),
        voicevox=_load_voicevox_config(data),
        speech=_load_speech_config(data),
        audio=_load_audio_config(data),
        voice_profiles=_load_voice_profiles(data),
    )


def _load_json(path: Path) -> dict:
    """
    JSONファイルを読み込む。
    """

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_scopes(data: dict) -> list[AuthScope]:
    """
    config.json の文字列スコープを AuthScope に変換する。
    """

    scopes = []

    for scope_name in data["scopes"]:
        if scope_name not in _SCOPE_MAP:
            raise ValueError(
                f"Unknown Twitch scope: {scope_name}"
            )

        scopes.append(
            _SCOPE_MAP[scope_name]
        )

    return scopes

def _load_tts_config(data: dict) -> TtsConfig:
    """
    TTSエンジン設定を読み込む。
    """

    tts = data.get(
        "tts",
        {}
    )

    return TtsConfig(
        backend=tts.get(
            "backend",
            "aivis",
        ),
    )

def _load_aivis_config(data: dict) -> AivisConfig:
    """
    AivisSpeech Engine の接続設定を読み込む。
    """

    aivis = data["aivis"]

    return AivisConfig(
        host=aivis["host"],
        port=aivis["port"],
    )

def _load_voicevox_config(data: dict) -> VoicevoxConfig:
    """
    VOICEVOX Engine の接続設定を読み込む。
    """

    voicevox = data.get(
        "voicevox",
        {},
    )

    return VoicevoxConfig(
        host=voicevox.get(
            "host",
            "127.0.0.1",
        ),
        port=voicevox.get(
            "port",
            50021,
        ),
    )

def _load_speech_config(data: dict) -> SpeechConfig:
    """
    読み上げポリシー設定を読み込む。
    """

    speech = data["speech"]

    return SpeechConfig(
        max_length=speech["max_length"],
        cooldown=speech["cooldown"],
        skip_url_only=speech["skip_url_only"],
        skip_empty=speech["skip_empty"],
    )


def _load_audio_config(data: dict) -> AudioConfig:
    """
    音声出力設定を読み込む。
    """

    audio = data["audio"]

    return AudioConfig(
        backend=audio.get(
            "backend",
            "pipewire",
        ),
        app_name=audio.get(
            "app_name",
            "AivisVoiceBridge",
        ),
        media_role=audio.get(
            "media_role",
            "Communication",
        ),
    )


def _load_voice_profiles(data: dict) -> dict[str, VoiceProfile]:
    """
    読み上げ用の音声プロファイルを読み込む。
    """

    profiles = {}

    for name, profile in data["voices"].items():
        profiles[name] = VoiceProfile(
            name=name,
            speaker=profile["speaker"],
            speed=profile.get(
                "speed",
                1.0,
            ),
            pitch=profile.get(
                "pitch",
                0.0,
            ),
            volume=profile.get(
                "volume",
                1.0,
            ),
            enabled=profile.get(
                "enabled",
                True,
            ),
        )

    return profiles