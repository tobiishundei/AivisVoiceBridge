import json
import shutil
import socket
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from flask import Flask, Response, jsonify, render_template, request


app = Flask(__name__)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "settings" / "config.json"
CONFIG_BACKUP_PATH = PROJECT_ROOT / "settings" / "config.json.backup"
VERSION_PATH = PROJECT_ROOT / "VERSION"
DICTIONARIES_ROOT = PROJECT_ROOT / "dictionaries"

COMMON_DICTIONARY_DIR = (
    DICTIONARIES_ROOT / "common"
)

GAME_DICTIONARY_DIR = (
    DICTIONARIES_ROOT / "game"
)

PERSONAL_DICTIONARY_DIR = (
    DICTIONARIES_ROOT / "personal"
)
TOKEN_BACKUP_SUFFIX = ".reauth-backup"
AUTH_STATUS_FILENAME = "auth_status.json"
VOICE_PROFILE_NAMES = {
    "default": "通常ユーザー",
    "broadcaster": "配信者",
    "moderator": "モデレーター",
    "vip": "VIP",
    "subscriber": "サブスクライバー",
}

TTS_BACKEND_NAMES = {
    "aivis": "AivisSpeech Engine",
    "voicevox": "VOICEVOX Engine",
}

DEFAULT_ENGINE_PORTS = {
    "aivis": 10101,
    "voicevox": 50021,
}

def get_app_version() -> str:
    """
    VERSIONファイルから
    AivisVoiceBridgeのバージョンを取得する。
    """
    if not VERSION_PATH.exists():
        return "development"

    try:
        version = VERSION_PATH.read_text(
            encoding="utf-8"
        ).strip()

    except OSError:
        return "development"

    return version or "development"

def load_config() -> dict[str, Any]:
    """
    settings/config.jsonを読み込む。
    """
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            "settings/config.json が見つかりません。"
            " config.json.example をコピーして作成してください。"
        )

    try:
        with CONFIG_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            config = json.load(file)

    except json.JSONDecodeError as error:
        raise ValueError(
            "settings/config.json のJSON形式が正しくありません。"
        ) from error

    if not isinstance(config, dict):
        raise ValueError(
            "settings/config.json のルートは"
            "JSONオブジェクトである必要があります。"
        )

    return config


def save_config(
    config: dict[str, Any],
) -> None:
    """
    設定ファイルを安全に保存する。

    1. 現在のconfig.jsonをバックアップ
    2. 一時ファイルへ新しい設定を書き込む
    3. 一時ファイルをconfig.jsonへ置き換える
    """
    temporary_path = CONFIG_PATH.with_suffix(
        ".json.tmp"
    )

    if CONFIG_PATH.exists():
        shutil.copy2(
            CONFIG_PATH,
            CONFIG_BACKUP_PATH,
        )

    try:
        with temporary_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                config,
                file,
                ensure_ascii=False,
                indent=2,
            )

            file.write("\n")

        temporary_path.replace(CONFIG_PATH)

    except OSError:
        if temporary_path.exists():
            temporary_path.unlink()

        raise

def resolve_project_path(
    configured_path: Any,
) -> Path:
    """
    config.json内のパスを
    プロジェクト直下基準の絶対パスへ変換する。
    """
    path = Path(
        str(configured_path).strip()
    )

    if path.is_absolute():
        return path

    return PROJECT_ROOT / path

def get_twitch_auth_status(
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    Twitchトークンファイルと、
    本体が記録した認証ユーザー情報を確認する。
    """
    token_path = resolve_project_path(
        config.get(
            "token_file",
            "tokens/user_token.json",
        )
    )

    status_path = (
        token_path.parent
        / AUTH_STATUS_FILENAME
    )

    token_exists = (
        token_path.is_file()
        and token_path.stat().st_size > 0
    )

    status: dict[str, Any] = {
        "token_path": str(token_path),
        "token_exists": token_exists,
        "status_path": str(status_path),
        "authenticated": False,
        "login": None,
        "display_name": None,
        "user_id": None,
        "checked_at": None,
        "message": "",
    }

    if not token_exists:
        status["message"] = (
            "トークンファイルがありません。"
            " AivisVoiceBridgeを起動すると"
            "認証が開始されます。"
        )

        return status

    if not status_path.exists():
        status["message"] = (
            "トークンファイルは存在しますが、"
            "認証ユーザー情報はまだ記録されていません。"
            " AivisVoiceBridgeを一度起動してください。"
        )

        return status

    try:
        with status_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            saved_status = json.load(file)

    except (
        OSError,
        json.JSONDecodeError,
    ):
        status["message"] = (
            "認証状態ファイルを"
            "読み取れませんでした。"
        )

        return status

    if not isinstance(saved_status, dict):
        status["message"] = (
            "認証状態ファイルの形式が"
            "正しくありません。"
        )

        return status

    status["authenticated"] = bool(
        saved_status.get(
            "authenticated",
            False,
        )
    )

    status["login"] = saved_status.get(
        "login"
    )

    status["display_name"] = (
        saved_status.get("display_name")
    )

    status["user_id"] = saved_status.get(
        "user_id"
    )

    status["checked_at"] = (
        saved_status.get("checked_at")
    )

    if status["authenticated"]:
        status["message"] = (
            "前回のAivisVoiceBridge起動時に"
            "Twitch認証が成功しています。"
        )
    else:
        status["message"] = (
            "Twitch認証済みであることを"
            "確認できませんでした。"
        )

    return status

def get_engine_information(
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    設定から現在の音声エンジン情報を取得する。
    """
    tts_config = config.get("tts", {})

    if not isinstance(tts_config, dict):
        tts_config = {}

    backend = str(
        tts_config.get("backend", "aivis")
    ).lower()

    if backend == "aivis":
        engine_name = "AivisSpeech Engine"
        engine_config = config.get("aivis", {})

    elif backend == "voicevox":
        engine_name = "VOICEVOX Engine"
        engine_config = config.get("voicevox", {})

    else:
        engine_name = f"不明なエンジン（{backend}）"
        engine_config = {}

    if not isinstance(engine_config, dict):
        engine_config = {}

    host = str(
        engine_config.get("host", "127.0.0.1")
    )

    try:
        port = int(
            engine_config.get("port", 0)
        )
    except (TypeError, ValueError):
        port = 0

    if port > 0:
        base_url = f"http://{host}:{port}"
    else:
        base_url = ""

    return {
        "backend": backend,
        "engine_name": engine_name,
        "host": host,
        "port": port,
        "base_url": base_url,
    }


def get_engine_information_by_backend(
    config: dict[str, Any],
    backend: str,
) -> dict[str, Any]:
    """
    指定されたbackendの接続情報を取得する。
    """
    backend = str(backend).strip().lower()

    if backend not in TTS_BACKEND_NAMES:
        raise ValueError(
            "音声エンジンが正しくありません。"
        )

    engine_config = config.get(
        backend,
        {},
    )

    if not isinstance(engine_config, dict):
        engine_config = {}

    host = str(
        engine_config.get(
            "host",
            "127.0.0.1",
        )
    ).strip()

    default_port = DEFAULT_ENGINE_PORTS[
        backend
    ]

    try:
        port = int(
            engine_config.get(
                "port",
                default_port,
            )
        )

    except (TypeError, ValueError):
        port = default_port

    if not 1 <= port <= 65535:
        port = default_port

    return {
        "backend": backend,
        "engine_name": TTS_BACKEND_NAMES[backend],
        "host": host,
        "port": port,
        "base_url": f"http://{host}:{port}",
    }


def get_voice_settings(
    config: dict[str, Any],
    profile_name: str,
) -> dict[str, Any]:
    """
    指定されたvoicesプロフィールから
    現在の音声設定を取得する。
    """
    settings = {
        "backend": str(
            config.get(
                "tts",
                {},
            ).get(
                "backend",
                "aivis",
            )
        ),
        "speaker": None,
        "speed": 1.0,
        "pitch": 0.0,
        "volume": 1.0,
        "enabled": True,
    }

    voices = config.get("voices", {})

    if not isinstance(voices, dict):
        return settings

    voice_profile = voices.get(
        profile_name,
        {},
    )

    if not isinstance(voice_profile, dict):
        return settings

    backend = str(
        voice_profile.get(
            "backend",
            settings["backend"],
        )
    ).strip().lower()

    if backend in TTS_BACKEND_NAMES:
        settings["backend"] = backend

    speaker_id = voice_profile.get("speaker")

    if not isinstance(speaker_id, bool):
        try:
            settings["speaker"] = int(
                speaker_id
            )
        except (TypeError, ValueError):
            pass

    try:
        speed = float(
            voice_profile.get("speed", 1.0)
        )

        if 0.5 <= speed <= 2.0:
            settings["speed"] = speed

    except (TypeError, ValueError):
        pass

    try:
        pitch = float(
            voice_profile.get("pitch", 0.0)
        )

        if -0.15 <= pitch <= 0.15:
            settings["pitch"] = pitch

    except (TypeError, ValueError):
        pass

    try:
        volume = float(
            voice_profile.get("volume", 1.0)
        )

        if 0.0 <= volume <= 2.0:
            settings["volume"] = volume

    except (TypeError, ValueError):
        pass

    enabled = voice_profile.get(
        "enabled",
        True,
    )

    if isinstance(enabled, bool):
        settings["enabled"] = enabled

    return settings

def get_twitch_settings(
    config: dict[str, Any],
) -> dict[str, str]:
    """
    Twitch接続に関する基本設定を取得する。
    """
    channel = str(
        config.get("channel", "")
    ).strip()

    redirect_uri = str(
        config.get(
            "redirect_uri",
            "http://localhost:17563",
        )
    ).strip()

    return {
        "channel": channel,
        "redirect_uri": redirect_uri,
    }

def get_available_game_dictionaries() -> list[str]:
    """
    dictionaries/game直下にある
    ゲーム辞書ディレクトリ名を取得する。
    """
    if not GAME_DICTIONARY_DIR.is_dir():
        return []

    dictionaries: list[str] = []

    for directory in sorted(
        GAME_DICTIONARY_DIR.iterdir(),
        key=lambda path: path.name.lower(),
    ):
        if not directory.is_dir():
            continue

        dictionaries.append(
            directory.name
        )

    return dictionaries

def inspect_dictionary_directory(
    directory: Path,
) -> dict[str, Any]:
    """
    指定ディレクトリ内のJSON辞書を検査する。

    ファイル数、登録語数、エラー内容、
    統合された辞書データを返す。
    """
    result: dict[str, Any] = {
        "directory": str(directory),
        "exists": directory.is_dir(),
        "file_count": 0,
        "entry_count": 0,
        "files": [],
        "errors": [],
        "merged_entries": {},
    }

    if not directory.is_dir():
        result["errors"].append(
            "辞書ディレクトリが存在しません。"
        )

        return result

    json_files = sorted(
        directory.rglob("*.json"),
        key=lambda path: str(path).lower(),
    )

    result["file_count"] = len(json_files)

    if not json_files:
        result["errors"].append(
            "JSON辞書ファイルがありません。"
        )

        return result

    merged_entries: dict[str, str] = {}

    for file_path in json_files:
        relative_path = file_path.relative_to(
            DICTIONARIES_ROOT
        )

        file_result: dict[str, Any] = {
            "path": str(relative_path),
            "entry_count": 0,
            "success": False,
            "error": None,
        }

        try:
            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            if not isinstance(data, dict):
                raise ValueError(
                    "JSONのルートはオブジェクトである"
                    "必要があります。"
                )

            normalized_data: dict[str, str] = {}

            for before, after in data.items():
                if not isinstance(before, str):
                    raise ValueError(
                        "変換前の値は文字列である"
                        "必要があります。"
                    )

                if not isinstance(after, str):
                    raise ValueError(
                        f"「{before}」の変換後の値は"
                        "文字列である必要があります。"
                    )

                normalized_data[before] = after

            file_result["entry_count"] = len(
                normalized_data
            )

            file_result["success"] = True

            merged_entries.update(
                normalized_data
            )

        except (
            OSError,
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
        ) as error:
            file_result["error"] = str(error)

            result["errors"].append(
                f"{relative_path}: {error}"
            )

        result["files"].append(
            file_result
        )

    result["merged_entries"] = merged_entries
    result["entry_count"] = len(
        merged_entries
    )

    return result

def get_dictionary_status(
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    現在選択されている辞書と、
    共通・ゲーム・個人辞書の状態を取得する。
    """
    selected_game = str(
        config.get(
            "game_dictionary",
            "",
        )
    ).strip()

    available_games = (
        get_available_game_dictionaries()
    )

    common_status = (
        inspect_dictionary_directory(
            COMMON_DICTIONARY_DIR
        )
    )

    personal_status = (
        inspect_dictionary_directory(
            PERSONAL_DICTIONARY_DIR
        )
    )

    if selected_game:
        selected_game_directory = (
            GAME_DICTIONARY_DIR
            / selected_game
        )

        game_status = (
            inspect_dictionary_directory(
                selected_game_directory
            )
        )

    else:
        game_status = {
            "directory": "",
            "exists": False,
            "file_count": 0,
            "entry_count": 0,
            "files": [],
            "errors": [
                "ゲーム辞書が選択されていません。"
            ],
            "merged_entries": {},
        }

    effective_entries: dict[str, str] = {}

    effective_entries.update(
        common_status["merged_entries"]
    )

    effective_entries.update(
        game_status["merged_entries"]
    )

    effective_entries.update(
        personal_status["merged_entries"]
    )

    all_errors = [
        *common_status["errors"],
        *game_status["errors"],
        *personal_status["errors"],
    ]

    return {
        "selected_game": selected_game,
        "available_games": available_games,
        "common": common_status,
        "game": game_status,
        "personal": personal_status,
        "effective_entry_count": len(
            effective_entries
        ),
        "has_errors": bool(all_errors),
        "errors": all_errors,
    }

def parse_game_dictionary(
    value: Any,
) -> str:
    """
    選択されたゲーム辞書名を検証する。
    """
    game_dictionary = str(value).strip()

    if not game_dictionary:
        raise ValueError(
            "ゲーム辞書を選択してください。"
        )

    available_games = (
        get_available_game_dictionaries()
    )

    if game_dictionary not in available_games:
        raise ValueError(
            "選択されたゲーム辞書は"
            "存在しません。"
        )

    return game_dictionary

def update_dictionary_settings(
    config: dict[str, Any],
    game_dictionary: str,
) -> None:
    """
    使用するゲーム辞書を更新する。
    """
    config["game_dictionary"] = (
        game_dictionary
    )

def get_speech_settings(
    config: dict[str, Any],
) -> dict[str, Any]:
    """
    speechセクションから読み上げ基本設定を取得する。
    """
    settings = {
        "max_length": 120,
        "cooldown": 3.0,
        "skip_url_only": True,
        "skip_empty": True,
    }

    speech_config = config.get("speech", {})

    if not isinstance(speech_config, dict):
        return settings

    max_length = speech_config.get(
        "max_length",
        120,
    )

    if not isinstance(max_length, bool):
        try:
            parsed_max_length = int(max_length)

            if 1 <= parsed_max_length <= 1000:
                settings["max_length"] = (
                    parsed_max_length
                )

        except (TypeError, ValueError):
            pass

    cooldown = speech_config.get(
        "cooldown",
        3.0,
    )

    if not isinstance(cooldown, bool):
        try:
            parsed_cooldown = float(cooldown)

            if 0.0 <= parsed_cooldown <= 60.0:
                settings["cooldown"] = parsed_cooldown

        except (TypeError, ValueError):
            pass

    skip_url_only = speech_config.get(
        "skip_url_only",
        True,
    )

    if isinstance(skip_url_only, bool):
        settings["skip_url_only"] = skip_url_only

    skip_empty = speech_config.get(
        "skip_empty",
        True,
    )

    if isinstance(skip_empty, bool):
        settings["skip_empty"] = skip_empty

    return settings

def get_all_voice_profiles(
    config: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    """
    Web UIで扱う全音声プロフィールを取得する。
    """
    profiles: dict[str, dict[str, Any]] = {}

    for profile_name in VOICE_PROFILE_NAMES:
        profiles[profile_name] = get_voice_settings(
            config,
            profile_name,
        )

    return profiles

def update_voice_profile(
    config: dict[str, Any],
    profile_name: str,
    backend: str,
    speaker_id: int,
    speed: float,
    pitch: float,
    volume: float,
    enabled: bool,
) -> None:
    """
    指定されたvoicesプロフィールを更新する。
    """
    if profile_name not in VOICE_PROFILE_NAMES:
        raise ValueError(
            "保存対象の音声プロフィールが正しくありません。"
        )

    if backend not in TTS_BACKEND_NAMES:
        raise ValueError(
            "音声エンジンが正しくありません。"
        )

    voices = config.get("voices")

    if not isinstance(voices, dict):
        voices = {}
        config["voices"] = voices

    voice_profile = voices.get(profile_name)

    if not isinstance(voice_profile, dict):
        voice_profile = {}
        voices[profile_name] = voice_profile

    voice_profile["backend"] = backend
    voice_profile["speaker"] = speaker_id
    voice_profile["speed"] = speed
    voice_profile["pitch"] = pitch
    voice_profile["volume"] = volume
    voice_profile["enabled"] = enabled


def request_json(
    url: str,
    timeout: float = 3,
) -> Any:
    """
    指定URLへGETリクエストを送り、
    JSONレスポンスをPythonの値へ変換する。
    """
    with urlopen(
        url,
        timeout=timeout,
    ) as response:
        response_text = (
            response.read()
            .decode("utf-8")
            .strip()
        )

    try:
        return json.loads(response_text)

    except json.JSONDecodeError as error:
        raise ValueError(
            "音声エンジンからJSON形式ではない"
            "応答が返されました。"
        ) from error

def post_json(
    url: str,
    data: Any,
    timeout: float = 10,
) -> Any:
    """
    JSONをPOSTし、JSONレスポンスを取得する。
    """
    body = json.dumps(
        data,
        ensure_ascii=False,
    ).encode("utf-8")

    url_request = UrlRequest(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
        },
    )

    with urlopen(
        url_request,
        timeout=timeout,
    ) as response:
        response_text = (
            response.read()
            .decode("utf-8")
            .strip()
        )

    try:
        return json.loads(response_text)

    except json.JSONDecodeError as error:
        raise ValueError(
            "音声エンジンからJSON形式ではない"
            "応答が返されました。"
        ) from error


def post_for_binary(
    url: str,
    data: Any,
    timeout: float = 30,
) -> bytes:
    """
    JSONをPOSTし、音声などのバイナリデータを取得する。
    """
    body = json.dumps(
        data,
        ensure_ascii=False,
    ).encode("utf-8")

    url_request = UrlRequest(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
        },
    )

    with urlopen(
        url_request,
        timeout=timeout,
    ) as response:
        return response.read()

def parse_float_setting(
    value: Any,
    setting_name: str,
    minimum: float,
    maximum: float,
) -> float:
    """
    Web UIから送られた音声設定をfloatへ変換し、
    許可範囲内か確認する。
    """
    if isinstance(value, bool):
        raise ValueError(
            f"{setting_name}の値が正しくありません。"
        )

    try:
        parsed_value = float(value)

    except (TypeError, ValueError) as error:
        raise ValueError(
            f"{setting_name}の値が正しくありません。"
        ) from error

    if not minimum <= parsed_value <= maximum:
        raise ValueError(
            f"{setting_name}は"
            f"{minimum}～{maximum}の範囲で指定してください。"
        )

    return parsed_value

def parse_engine_host(
    value: Any,
) -> str:
    """
    音声エンジンのホスト名を検証する。

    localhost、IPアドレス、一般的なホスト名を想定する。
    URLやパスは受け付けない。
    """
    host = str(value).strip()

    if not host:
        raise ValueError(
            "ホストを入力してください。"
        )

    if len(host) > 253:
        raise ValueError(
            "ホスト名が長すぎます。"
        )

    forbidden_characters = {
        "/",
        "\\",
        ":",
        "?",
        "#",
        "@",
        " ",
        "\t",
        "\n",
    }

    if any(
        character in host
        for character in forbidden_characters
    ):
        raise ValueError(
            "ホストにはURLやポートを含めず、"
            "ホスト名またはIPアドレスだけを入力してください。"
        )

    return host

def parse_twitch_channel(
    value: Any,
) -> str:
    """
    Twitchチャンネル名を検証する。

    URLではなく、チャンネル名だけを保存する。
    """
    channel = str(value).strip()

    if not channel:
        raise ValueError(
            "Twitchチャンネル名を入力してください。"
        )

    if len(channel) > 25:
        raise ValueError(
            "Twitchチャンネル名が長すぎます。"
        )

    allowed_characters = set(
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "0123456789_"
    )

    if any(
        character not in allowed_characters
        for character in channel
    ):
        raise ValueError(
            "Twitchチャンネル名には、"
            "半角英数字とアンダースコアだけを使用してください。"
        )

    return channel.lower()

def parse_redirect_uri(
    value: Any,
) -> str:
    """
    Twitch認証用Redirect URIを検証する。
    """
    redirect_uri = str(value).strip()

    if not redirect_uri:
        raise ValueError(
            "Redirect URIを入力してください。"
        )

    if len(redirect_uri) > 500:
        raise ValueError(
            "Redirect URIが長すぎます。"
        )

    if not (
        redirect_uri.startswith("http://")
        or redirect_uri.startswith("https://")
    ):
        raise ValueError(
            "Redirect URIは"
            "http:// または https:// から始めてください。"
        )

    if any(
        character in redirect_uri
        for character in ("\n", "\r", "\t", " ")
    ):
        raise ValueError(
            "Redirect URIに空白や改行は使用できません。"
        )

    return redirect_uri

def parse_speech_max_length(
    value: Any,
) -> int:
    """
    最大読み上げ文字数を検証する。
    """
    if isinstance(value, bool):
        raise ValueError(
            "最大読み上げ文字数が正しくありません。"
        )

    try:
        max_length = int(value)

    except (TypeError, ValueError) as error:
        raise ValueError(
            "最大読み上げ文字数は整数で"
            "入力してください。"
        ) from error

    if not 1 <= max_length <= 1000:
        raise ValueError(
            "最大読み上げ文字数は"
            "1～1000の範囲で指定してください。"
        )

    return max_length


def parse_speech_cooldown(
    value: Any,
) -> float:
    """
    コメント間の読み上げ間隔を検証する。
    """
    if isinstance(value, bool):
        raise ValueError(
            "読み上げ間隔が正しくありません。"
        )

    try:
        cooldown = float(value)

    except (TypeError, ValueError) as error:
        raise ValueError(
            "読み上げ間隔は数値で入力してください。"
        ) from error

    if not 0.0 <= cooldown <= 60.0:
        raise ValueError(
            "読み上げ間隔は"
            "0～60秒の範囲で指定してください。"
        )

    return cooldown

def update_speech_settings(
    config: dict[str, Any],
    max_length: int,
    cooldown: float,
    skip_url_only: bool,
    skip_empty: bool,
) -> None:
    """
    speechセクションの基本設定を更新する。
    """
    speech_config = config.get("speech")

    if not isinstance(speech_config, dict):
        speech_config = {}
        config["speech"] = speech_config

    speech_config["max_length"] = max_length
    speech_config["cooldown"] = cooldown
    speech_config["skip_url_only"] = skip_url_only
    speech_config["skip_empty"] = skip_empty

def update_twitch_settings(
    config: dict[str, Any],
    channel: str,
    redirect_uri: str,
) -> None:
    """
    TwitchチャンネルとRedirect URIを更新する。
    """
    config["channel"] = channel
    config["redirect_uri"] = redirect_uri

def parse_engine_port(
    value: Any,
) -> int:
    """
    音声エンジンのポート番号を検証する。
    """
    if isinstance(value, bool):
        raise ValueError(
            "ポート番号が正しくありません。"
        )

    try:
        port = int(value)

    except (TypeError, ValueError) as error:
        raise ValueError(
            "ポート番号が正しくありません。"
        ) from error

    if not 1 <= port <= 65535:
        raise ValueError(
            "ポート番号は1～65535の範囲で"
            "指定してください。"
        )

    return port

def update_engine_settings(
    config: dict[str, Any],
    backend: str,
    host: str,
    port: int,
) -> None:
    """
    選択された音声エンジンと接続先を更新する。
    """
    if backend not in TTS_BACKEND_NAMES:
        raise ValueError(
            "音声エンジンの種類が正しくありません。"
        )

    tts_config = config.get("tts")

    if not isinstance(tts_config, dict):
        tts_config = {}
        config["tts"] = tts_config

    tts_config["backend"] = backend

    engine_config = config.get(backend)

    if not isinstance(engine_config, dict):
        engine_config = {}
        config[backend] = engine_config

    engine_config["host"] = host
    engine_config["port"] = port

def format_version(version: Any) -> str:
    """
    /versionの応答を画面表示用の文字列に変換する。
    """
    if isinstance(version, str):
        return version

    return json.dumps(
        version,
        ensure_ascii=False,
    )


def normalize_speakers(
    speakers_data: Any,
) -> list[dict[str, Any]]:
    """
    /speakersの応答を画面表示用に整形する。
    """
    if not isinstance(speakers_data, list):
        raise ValueError(
            "話者一覧の応答形式が正しくありません。"
        )

    normalized_speakers: list[dict[str, Any]] = []

    for speaker in speakers_data:
        if not isinstance(speaker, dict):
            continue

        speaker_name = str(
            speaker.get("name", "名前不明")
        )

        speaker_uuid = str(
            speaker.get("speaker_uuid", "")
        )

        styles_data = speaker.get("styles", [])

        if not isinstance(styles_data, list):
            styles_data = []

        normalized_styles: list[dict[str, Any]] = []

        for style in styles_data:
            if not isinstance(style, dict):
                continue

            style_name = str(
                style.get("name", "スタイル名不明")
            )

            style_id = style.get("id")

            if isinstance(style_id, bool):
                continue

            try:
                style_id = int(style_id)
            except (TypeError, ValueError):
                continue

            normalized_styles.append({
                "name": style_name,
                "id": style_id,
            })

        normalized_speakers.append({
            "name": speaker_name,
            "speaker_uuid": speaker_uuid,
            "styles": normalized_styles,
        })

    return normalized_speakers


def find_style(
    speakers: list[dict[str, Any]],
    style_id: int,
) -> dict[str, str] | None:
    """
    話者一覧から指定されたスタイルIDを探す。
    """
    for speaker in speakers:
        styles = speaker.get("styles", [])

        if not isinstance(styles, list):
            continue

        for style in styles:
            if style.get("id") == style_id:
                return {
                    "speaker_name": str(
                        speaker.get("name", "名前不明")
                    ),
                    "style_name": str(
                        style.get("name", "スタイル名不明")
                    ),
                }

    return None


def check_engine_and_get_speakers(
    engine: dict[str, Any],
) -> dict[str, Any]:
    """
    音声エンジンの接続確認を行い、
    成功した場合は話者一覧も取得する。
    """
    base_url = engine.get("base_url", "")

    if not base_url:
        return {
            "success": False,
            "message": "接続先が正しく設定されていません。",
            "version": None,
            "speakers": [],
        }

    version_url = f"{base_url}/version"
    speakers_url = f"{base_url}/speakers"

    try:
        version_data = request_json(
            version_url,
            timeout=3,
        )

        speakers_data = request_json(
            speakers_url,
            timeout=5,
        )

        speakers = normalize_speakers(
            speakers_data
        )

        return {
            "success": True,
            "message": (
                f"{engine['engine_name']} に接続できました。"
            ),
            "version": format_version(version_data),
            "speakers": speakers,
        }

    except HTTPError as error:
        return {
            "success": False,
            "message": (
                "音声エンジンからHTTPエラーが返されました。"
                f" ステータスコード: {error.code}"
            ),
            "version": None,
            "speakers": [],
        }

    except URLError as error:
        reason = error.reason

        if isinstance(reason, ConnectionRefusedError):
            detail = "接続が拒否されました。"
        else:
            detail = str(reason)

        return {
            "success": False,
            "message": (
                f"{engine['engine_name']} に接続できませんでした。"
                f" {detail}"
            ),
            "version": None,
            "speakers": [],
        }

    except (TimeoutError, socket.timeout):
        return {
            "success": False,
            "message": (
                "音声エンジンへの接続が"
                "タイムアウトしました。"
            ),
            "version": None,
            "speakers": [],
        }

    except UnicodeDecodeError:
        return {
            "success": False,
            "message": (
                "音声エンジンからの応答を"
                "読み取れませんでした。"
            ),
            "version": None,
            "speakers": [],
        }

    except ValueError as error:
        return {
            "success": False,
            "message": str(error),
            "version": None,
            "speakers": [],
        }


def render_index(
    connection_result: dict[str, Any] | None = None,
    save_result: dict[str, Any] | None = None,
):
    """
    設定画面を表示するための共通処理。
    """
    try:
        config = load_config()
        engine = get_engine_information(config)
        voice_profiles = get_all_voice_profiles(
            config
        )
        speech_settings = get_speech_settings(
            config
        )
        twitch_settings = get_twitch_settings(
            config
        )
        twitch_auth_status = (
            get_twitch_auth_status(config)
        )
        dictionary_status = (
            get_dictionary_status(config)
        )
        return render_template(
            "index.html",
            config_loaded=True,
            error_message=None,
            engine=engine,
            config_path=str(CONFIG_PATH),
            backup_path=str(CONFIG_BACKUP_PATH),
            connection_result=connection_result,
            save_result=save_result,
            voice_profiles=voice_profiles,
            voice_profile_names=VOICE_PROFILE_NAMES,
            tts_backend_names=TTS_BACKEND_NAMES,
            default_engine_ports=DEFAULT_ENGINE_PORTS,
            speech_settings=speech_settings,
            twitch_settings=twitch_settings,
            twitch_auth_status=twitch_auth_status,
            dictionary_status=dictionary_status,
            app_version=get_app_version(),
        )

    except (FileNotFoundError, ValueError) as error:
        return render_template(
            "index.html",
            config_loaded=False,
            error_message=str(error),
            engine=None,
            config_path=str(CONFIG_PATH),
            backup_path=str(CONFIG_BACKUP_PATH),
            connection_result=None,
            save_result=save_result,
            voice_profiles={},
            voice_profile_names=VOICE_PROFILE_NAMES,
            tts_backend_names=TTS_BACKEND_NAMES,
            default_engine_ports=DEFAULT_ENGINE_PORTS,
            speech_settings={
                "max_length": 120,
                "cooldown": 3.0,
                "skip_url_only": True,
                "skip_empty": True,
            },
            twitch_settings={
                "channel": "",
                "redirect_uri": "http://localhost:17563",
            },
            twitch_auth_status={
                "token_path": "",
                "token_exists": False,
                "status_path": "",
                "authenticated": False,
                "login": None,
                "display_name": None,
                "user_id": None,
                "checked_at": None,
                "message": (
                    "設定ファイルを読み込めないため、"
                    "認証状態を確認できません。"
                ),
            },
            dictionary_status={
                "selected_game": "",
                "available_games": [],
                "common": {
                    "directory": str(
                        COMMON_DICTIONARY_DIR
                    ),
                    "exists": False,
                    "file_count": 0,
                    "entry_count": 0,
                    "files": [],
                    "errors": [],
                },
                "game": {
                    "directory": "",
                    "exists": False,
                    "file_count": 0,
                    "entry_count": 0,
                    "files": [],
                    "errors": [],
                },
                "personal": {
                    "directory": str(
                        PERSONAL_DICTIONARY_DIR
                    ),
                    "exists": False,
                    "file_count": 0,
                    "entry_count": 0,
                    "files": [],
                    "errors": [],
                },
                "effective_entry_count": 0,
                "has_errors": True,
                "errors": [
                    "設定ファイルを読み込めないため、"
                    "辞書状態を確認できません。"
                ],
            },
            app_version=get_app_version(),
        )

@app.post("/prepare-twitch-reauth")
def prepare_twitch_reauth():
    """
    現在のTwitchトークンをバックアップし、
    次回起動時に再認証される状態へ戻す。
    """
    try:
        config = load_config()

        token_path = resolve_project_path(
            config.get(
                "token_file",
                "tokens/user_token.json",
            )
        )

        status_path = (
            token_path.parent
            / AUTH_STATUS_FILENAME
        )

        backup_path = Path(
            f"{token_path}{TOKEN_BACKUP_SUFFIX}"
        )

        if not token_path.exists():
            return render_index(
                save_result={
                    "success": False,
                    "message": (
                        "トークンファイルがないため、"
                        "再認証準備は不要です。"
                        " AivisVoiceBridgeを起動すると"
                        "認証が開始されます。"
                    ),
                }
            )

        token_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if backup_path.exists():
            backup_path.unlink()

        token_path.replace(
            backup_path
        )

        if status_path.exists():
            status_path.unlink()

        return render_index(
            save_result={
                "success": True,
                "message": (
                    "Twitch再認証の準備ができました。"
                    " AivisVoiceBridge本体を再起動すると、"
                    "ブラウザ認証が開始されます。"
                    f" 以前のトークンは"
                    f" {backup_path} に退避しました。"
                ),
            }
        )

    except (
        FileNotFoundError,
        ValueError,
        OSError,
    ) as error:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    "Twitch再認証の準備に"
                    f"失敗しました。 {error}"
                ),
            }
        )

@app.get("/")
def index():
    """
    AivisVoiceBridgeの設定画面を表示する。
    """
    return render_index()


@app.post("/check-engine")
def check_engine():
    """
    現在設定されている音声エンジンへ接続し、
    話者一覧を取得する。
    """
    try:
        config = load_config()
        engine = get_engine_information(config)

        connection_result = (
            check_engine_and_get_speakers(engine)
        )

    except (FileNotFoundError, ValueError) as error:
        connection_result = {
            "success": False,
            "message": str(error),
            "version": None,
            "speakers": [],
        }

    return render_index(
        connection_result=connection_result,
    )


@app.get("/api/engine-speakers/<backend>")
def api_engine_speakers(
    backend: str,
):
    """
    指定されたTTSエンジンへ接続し、
    話者・スタイル一覧を返す。
    """
    try:
        config = load_config()

        engine = (
            get_engine_information_by_backend(
                config,
                backend,
            )
        )

        result = (
            check_engine_and_get_speakers(
                engine
            )
        )

        status_code = (
            200
            if result["success"]
            else 502
        )

        return jsonify(result), status_code

    except (
        FileNotFoundError,
        ValueError,
        OSError,
    ) as error:
        return jsonify({
            "success": False,
            "message": str(error),
            "version": None,
            "speakers": [],
        }), 400


@app.post("/save-voice-profile")
def save_voice_profile():
    """
    選択された役割の音声設定を保存する。
    """
    profile_name = request.form.get(
        "profile_name",
        "",
    ).strip()

    if profile_name not in VOICE_PROFILE_NAMES:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    "保存対象の音声プロフィールが"
                    "正しくありません。"
                ),
            }
        )

    backend = request.form.get(
        "profile_backend",
        "",
    ).strip().lower()

    if backend not in TTS_BACKEND_NAMES:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    "音声エンジンが正しくありません。"
                ),
            }
        )

    raw_style_id = request.form.get(
        "style_id",
        "",
    ).strip()

    raw_speed = request.form.get(
        "speed",
        "",
    ).strip()

    raw_pitch = request.form.get(
        "pitch",
        "",
    ).strip()

    raw_volume = request.form.get(
        "volume",
        "",
    ).strip()

    raw_enabled = request.form.get(
        "enabled",
        "",
    )

    enabled = raw_enabled == "on"

    try:
        style_id = int(raw_style_id)

    except ValueError:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    "スタイルIDが正しくありません。"
                ),
            }
        )

    if style_id < 0:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    "スタイルIDが正しくありません。"
                ),
            }
        )

    try:
        speed = parse_float_setting(
            raw_speed,
            "話速",
            0.5,
            2.0,
        )

        pitch = parse_float_setting(
            raw_pitch,
            "音高",
            -0.15,
            0.15,
        )

        volume = parse_float_setting(
            raw_volume,
            "音量",
            0.0,
            2.0,
        )

    except ValueError as error:
        return render_index(
            save_result={
                "success": False,
                "message": str(error),
            }
        )

    try:
        config = load_config()
        engine = (
            get_engine_information_by_backend(
                config,
                backend,
            )
        )

        connection_result = (
            check_engine_and_get_speakers(engine)
        )

        if not connection_result["success"]:
            return render_index(
                connection_result=connection_result,
                save_result={
                    "success": False,
                    "message": (
                        "音声エンジンへ接続できないため、"
                        "設定を保存しませんでした。"
                    ),
                },
            )

        speakers = connection_result["speakers"]

        selected_style = find_style(
            speakers,
            style_id,
        )

        if selected_style is None:
            return render_index(
                connection_result=connection_result,
                save_result={
                    "success": False,
                    "message": (
                        "選択されたスタイルIDは、"
                        "現在の音声エンジンに存在しません。"
                    ),
                },
            )

        update_voice_profile(
            config=config,
            profile_name=profile_name,
            backend=backend,
            speaker_id=style_id,
            speed=speed,
            pitch=pitch,
            volume=volume,
            enabled=enabled,
        )

        save_config(config)

        speaker_name = (
            selected_style["speaker_name"]
        )

        style_name = (
            selected_style["style_name"]
        )

        profile_label = VOICE_PROFILE_NAMES[
            profile_name
        ]

        engine_label = TTS_BACKEND_NAMES[
            backend
        ]

        return render_index(
            connection_result=connection_result,
            save_result={
                "success": True,
                "message": (
                    f"「{profile_label}」の音声設定を"
                    f"「{engine_label} / "
                    f"{speaker_name} / {style_name}」"
                    f"へ変更しました。"
                    f" 話速: {speed:.2f}、"
                    f"音高: {pitch:.2f}、"
                    f"音量: {volume:.2f}、"
                    f"有効: {'はい' if enabled else 'いいえ'}"
                ),
            },
        )

    except (
        FileNotFoundError,
        ValueError,
        OSError,
    ) as error:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    f"設定を保存できませんでした。"
                    f" {error}"
                ),
            }
        )

@app.post("/save-engine-settings")
def save_engine_settings():
    """
    使用する音声エンジンと接続先を保存する。
    """
    backend = request.form.get(
        "backend",
        "",
    ).strip().lower()

    raw_host = request.form.get(
        "host",
        "",
    )

    raw_port = request.form.get(
        "port",
        "",
    )

    if backend not in TTS_BACKEND_NAMES:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    "音声エンジンの種類が"
                    "正しくありません。"
                ),
            }
        )

    try:
        host = parse_engine_host(
            raw_host
        )

        port = parse_engine_port(
            raw_port
        )

    except ValueError as error:
        return render_index(
            save_result={
                "success": False,
                "message": str(error),
            }
        )

    try:
        config = load_config()

        update_engine_settings(
            config=config,
            backend=backend,
            host=host,
            port=port,
        )

        save_config(config)

        updated_engine = (
            get_engine_information(config)
        )

        connection_result = (
            check_engine_and_get_speakers(
                updated_engine
            )
        )

        engine_label = TTS_BACKEND_NAMES[
            backend
        ]

        if connection_result["success"]:
            message = (
                f"音声エンジンを"
                f"「{engine_label}」へ変更しました。"
                f" 接続先: http://{host}:{port}"
            )

        else:
            message = (
                f"音声エンジン設定を"
                f"「{engine_label}」として保存しました。"
                f" ただし、現在は接続できません。"
                f" 接続先: http://{host}:{port}"
            )

        return render_index(
            connection_result=connection_result,
            save_result={
                "success": True,
                "message": message,
            },
        )

    except (
        FileNotFoundError,
        ValueError,
        OSError,
    ) as error:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    f"音声エンジン設定を"
                    f"保存できませんでした。 {error}"
                ),
            }
        )

@app.post("/save-speech-settings")
def save_speech_settings():
    """
    読み上げ基本設定を保存する。
    """
    raw_max_length = request.form.get(
        "max_length",
        "",
    ).strip()

    raw_cooldown = request.form.get(
        "cooldown",
        "",
    ).strip()

    skip_url_only = (
        request.form.get("skip_url_only") == "on"
    )

    skip_empty = (
        request.form.get("skip_empty") == "on"
    )

    try:
        max_length = parse_speech_max_length(
            raw_max_length
        )

        cooldown = parse_speech_cooldown(
            raw_cooldown
        )

    except ValueError as error:
        return render_index(
            save_result={
                "success": False,
                "message": str(error),
            }
        )

    try:
        config = load_config()

        update_speech_settings(
            config=config,
            max_length=max_length,
            cooldown=cooldown,
            skip_url_only=skip_url_only,
            skip_empty=skip_empty,
        )

        save_config(config)

        return render_index(
            save_result={
                "success": True,
                "message": (
                    "読み上げ基本設定を保存しました。"
                    f" 最大文字数: {max_length}、"
                    f"読み上げ間隔: {cooldown:.1f}秒、"
                    "URLのみを無視: "
                    f"{'はい' if skip_url_only else 'いいえ'}、"
                    "空コメントを無視: "
                    f"{'はい' if skip_empty else 'いいえ'}"
                ),
            }
        )

    except (
        FileNotFoundError,
        ValueError,
        OSError,
    ) as error:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    "読み上げ基本設定を"
                    f"保存できませんでした。 {error}"
                ),
            }
        )

@app.post("/save-twitch-settings")
def save_twitch_settings():
    """
    TwitchチャンネルとRedirect URIを保存する。
    """
    raw_channel = request.form.get(
        "channel",
        "",
    )

    raw_redirect_uri = request.form.get(
        "redirect_uri",
        "",
    )

    try:
        channel = parse_twitch_channel(
            raw_channel
        )

        redirect_uri = parse_redirect_uri(
            raw_redirect_uri
        )

    except ValueError as error:
        return render_index(
            save_result={
                "success": False,
                "message": str(error),
            }
        )

    try:
        config = load_config()

        update_twitch_settings(
            config=config,
            channel=channel,
            redirect_uri=redirect_uri,
        )

        save_config(config)

        return render_index(
            save_result={
                "success": True,
                "message": (
                    "Twitch設定を保存しました。"
                    f" チャンネル: {channel}、"
                    f"Redirect URI: {redirect_uri}"
                ),
            }
        )

    except (
        FileNotFoundError,
        ValueError,
        OSError,
    ) as error:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    "Twitch設定を保存できませんでした。"
                    f" {error}"
                ),
            }
        )

@app.post("/save-dictionary-settings")
def save_dictionary_settings():
    """
    使用するゲーム辞書を保存する。
    """
    raw_game_dictionary = request.form.get(
        "game_dictionary",
        "",
    )

    try:
        game_dictionary = (
            parse_game_dictionary(
                raw_game_dictionary
            )
        )

    except ValueError as error:
        return render_index(
            save_result={
                "success": False,
                "message": str(error),
            }
        )

    try:
        config = load_config()

        update_dictionary_settings(
            config=config,
            game_dictionary=game_dictionary,
        )

        save_config(config)

        dictionary_status = (
            get_dictionary_status(config)
        )

        if dictionary_status["has_errors"]:
            message = (
                f"ゲーム辞書を"
                f"「{game_dictionary}」へ変更しました。"
                " ただし、辞書ファイルに"
                "確認が必要な問題があります。"
            )
        else:
            message = (
                f"ゲーム辞書を"
                f"「{game_dictionary}」へ変更しました。"
                f" 有効な登録語数: "
                f"{dictionary_status['effective_entry_count']}語"
            )

        return render_index(
            save_result={
                "success": True,
                "message": message,
            }
        )

    except (
        FileNotFoundError,
        ValueError,
        OSError,
    ) as error:
        return render_index(
            save_result={
                "success": False,
                "message": (
                    "辞書設定を保存できませんでした。"
                    f" {error}"
                ),
            }
        )

@app.post("/test-speech")
def test_speech():
    """
    選択されたスタイルでテスト音声を生成し、
    WAVデータをブラウザへ返す。
    """
    request_data = request.get_json(
        silent=True,
    )

    if not isinstance(request_data, dict):
        return jsonify({
            "success": False,
            "message": "リクエスト形式が正しくありません。",
        }), 400

    backend = str(
        request_data.get(
            "backend",
            "",
        )
    ).strip().lower()

    if backend not in TTS_BACKEND_NAMES:
        return jsonify({
            "success": False,
            "message": (
                "音声エンジンが正しくありません。"
            ),
        }), 400

    text = str(
        request_data.get("text", "")
    ).strip()

    raw_style_id = request_data.get(
        "style_id"
    )

    raw_speed = request_data.get(
        "speed",
        1.0,
    )

    raw_pitch = request_data.get(
        "pitch",
        0.0,
    )

    raw_volume = request_data.get(
        "volume",
        1.0,
    )

    try:
        speed = parse_float_setting(
            raw_speed,
            "話速",
            0.5,
            2.0,
        )

        pitch = parse_float_setting(
            raw_pitch,
            "音高",
            -0.15,
            0.15,
        )

        volume = parse_float_setting(
            raw_volume,
            "音量",
            0.0,
            2.0,
        )

    except ValueError as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 400

    if not text:
        return jsonify({
            "success": False,
            "message": "テスト文章を入力してください。",
        }), 400

    if len(text) > 200:
        return jsonify({
            "success": False,
            "message": (
                "テスト文章は200文字以内にしてください。"
            ),
        }), 400

    if isinstance(raw_style_id, bool):
        return jsonify({
            "success": False,
            "message": "スタイルIDが正しくありません。",
        }), 400

    try:
        style_id = int(raw_style_id)

    except (TypeError, ValueError):
        return jsonify({
            "success": False,
            "message": "スタイルIDが正しくありません。",
        }), 400

    if style_id < 0:
        return jsonify({
            "success": False,
            "message": "スタイルIDが正しくありません。",
        }), 400

    try:
        config = load_config()
        engine = (
            get_engine_information_by_backend(
                config,
                backend,
            )
        )

        base_url = engine.get(
            "base_url",
            "",
        )

        if not base_url:
            return jsonify({
                "success": False,
                "message": (
                    "音声エンジンの接続先が"
                    "正しく設定されていません。"
                ),
            }), 400

        speakers_data = request_json(
            f"{base_url}/speakers",
            timeout=5,
        )

        speakers = normalize_speakers(
            speakers_data
        )

        selected_style = find_style(
            speakers,
            style_id,
        )

        if selected_style is None:
            return jsonify({
                "success": False,
                "message": (
                    "選択されたスタイルは、"
                    "現在の音声エンジンに存在しません。"
                ),
            }), 400

        audio_query_parameters = urlencode({
            "text": text,
            "speaker": style_id,
        })

        audio_query_url = (
            f"{base_url}/audio_query"
            f"?{audio_query_parameters}"
        )

        audio_query = post_json(
            audio_query_url,
            {},
            timeout=10,
        )

        if not isinstance(audio_query, dict):
            return jsonify({
                "success": False,
                "message": (
                    "音声クエリの応答形式が正しくありません。"
                ),
            }), 502

        audio_query["speedScale"] = speed
        audio_query["pitchScale"] = pitch
        audio_query["volumeScale"] = volume

        synthesis_parameters = urlencode({
            "speaker": style_id,
        })

        synthesis_url = (
            f"{base_url}/synthesis"
            f"?{synthesis_parameters}"
        )

        wav_data = post_for_binary(
            synthesis_url,
            audio_query,
            timeout=30,
        )

        if not wav_data:
            return jsonify({
                "success": False,
                "message": (
                    "音声エンジンから空の音声データが"
                    "返されました。"
                ),
            }), 502

        return Response(
            wav_data,
            status=200,
            mimetype="audio/wav",
            headers={
                "Content-Disposition": (
                    'inline; filename="test-speech.wav"'
                ),
                "Cache-Control": "no-store",
            },
        )

    except HTTPError as error:
        try:
            error_body = (
                error.read()
                .decode("utf-8")
                .strip()
            )
        except Exception:
            error_body = ""

        message = (
            "音声エンジンからHTTPエラーが返されました。"
            f" ステータスコード: {error.code}"
        )

        if error_body:
            message += f" 詳細: {error_body[:300]}"

        return jsonify({
            "success": False,
            "message": message,
        }), 502

    except URLError as error:
        reason = error.reason

        if isinstance(reason, ConnectionRefusedError):
            detail = "接続が拒否されました。"
        else:
            detail = str(reason)

        return jsonify({
            "success": False,
            "message": (
                f"{engine['engine_name']} に接続できませんでした。"
                f" {detail}"
            ),
        }), 502

    except (TimeoutError, socket.timeout):
        return jsonify({
            "success": False,
            "message": (
                "テスト音声の生成が"
                "タイムアウトしました。"
            ),
        }), 504

    except (
        FileNotFoundError,
        ValueError,
        UnicodeDecodeError,
    ) as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), 500

def main():
    """
    設定専用Webサーバーを起動する。
    """
    print("AivisVoiceBridge Web UI")
    print(
        "ブラウザで "
        "http://127.0.0.1:17564 "
        "を開いてください。"
    )

    app.run(
        host="127.0.0.1",
        port=17564,
        debug=False,
    )


if __name__ == "__main__":
    main()