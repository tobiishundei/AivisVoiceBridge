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


def get_voice_settings(
    config: dict[str, Any],
    profile_name: str,
) -> dict[str, Any]:
    """
    指定されたvoicesプロフィールから
    現在の音声設定を取得する。
    """
    settings = {
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

    voices = config.get("voices")

    if not isinstance(voices, dict):
        voices = {}
        config["voices"] = voices

    voice_profile = voices.get(profile_name)

    if not isinstance(voice_profile, dict):
        voice_profile = {}
        voices[profile_name] = voice_profile

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
        engine = get_engine_information(config)

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

        return render_index(
            connection_result=connection_result,
            save_result={
                "success": True,
                "message": (
                    f"「{profile_label}」の音声設定を"
                    f"「{speaker_name} / {style_name}」"
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
        engine = get_engine_information(config)

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