from dataclasses import dataclass
from pathlib import Path
import json

from models.voice_profile import VoiceProfile

from twitchAPI.type import AuthScope


@dataclass
class AivisConfig:
    host: str
    port: int


@dataclass
class SpeechConfig:
    max_length: int
    cooldown: float
    skip_url_only: bool
    skip_empty: bool


@dataclass
class AudioConfig:
    backend: str
    app_name: str
    media_role: str


@dataclass
class Config:
    client_id: str
    client_secret: str
    channel: str
    redirect_uri: str
    token_file: str
    scopes: list[AuthScope]

    game_dictionary: str

    aivis: AivisConfig
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


def _load_voice_profiles(data):

    profiles = {}

    for name, profile in data["voices"].items():

        profiles[name] = VoiceProfile(

            name=name,

            speaker=profile["speaker"],

            speed=profile["speed"],

            pitch=profile["pitch"],

            volume=profile["volume"],
        )

    return profiles


def load_config() -> Config:

    config_path = Path("settings") / "config.json"

    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    #
    # Aivis設定
    #
    aivis = AivisConfig(
        host=data["aivis"]["host"],
        port=data["aivis"]["port"],
    )

    #
    # Speech設定
    #
    speech = SpeechConfig(
        max_length=data["speech"]["max_length"],
        cooldown=data["speech"]["cooldown"],
        skip_url_only=data["speech"]["skip_url_only"],
        skip_empty=data["speech"]["skip_empty"],
    )

    #
    # Audio設定
    #
    audio_data = data["audio"]

    audio = AudioConfig(
        backend=audio_data.get(
            "backend",
            "pipewire",
        ),
        app_name=audio_data.get(
            "app_name",
            "AivisVoiceBridge",
        ),
        media_role=audio_data.get(
            "media_role",
            "Communication",
        ),
    )

    #
    # Config生成
    #
    return Config(
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        channel=data["channel"],
        redirect_uri=data["redirect_uri"],
        token_file=data["token_file"],
        scopes=[_SCOPE_MAP[s] for s in data["scopes"]],

        game_dictionary=data["game_dictionary"],

        aivis=aivis,
        speech=speech,
        audio=audio,
        voice_profiles=_load_voice_profiles(data),
    )