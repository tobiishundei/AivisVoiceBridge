"""
AivisVoiceBridge のエントリーポイント。

通常起動では Twitch コメント読み上げアプリを常駐起動する。
--audio-test を指定した場合は、OBS 初回設定用の長めの音声テストのみ実行する。
"""

import argparse
import asyncio

from commands.audio_test import run_audio_test
from core.application import Application
from core.config import load_config


def parse_args():
    """
    コマンドライン引数を解析する。
    """

    parser = argparse.ArgumentParser(
        description="AivisVoiceBridge"
    )

    parser.add_argument(
        "--audio-test",
        action="store_true",
        help="Play a long test voice for OBS audio setup",
    )

    return parser.parse_args()


async def run_application(config):
    """
    通常モードでアプリケーションを起動し、終了まで待機する。
    """

    app = Application(config)

    try:
        await app.start()

        while True:
            await asyncio.sleep(1)

    finally:
        await app.stop()


async def async_main():
    """
    起動モードを判定し、対応する処理を実行する。
    """

    args = parse_args()
    config = load_config()

    if args.audio_test:
        await run_audio_test(config)
        return

    await run_application(config)


if __name__ == "__main__":
    try:
        asyncio.run(async_main())

    except KeyboardInterrupt:
        pass