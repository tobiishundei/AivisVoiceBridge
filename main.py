import argparse
import asyncio

from core.application import Application
from core.config import load_config
from commands.audio_test import run_audio_test


async def async_main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--audio-test",
        action="store_true",
        help="Play a long test voice for OBS audio setup",
    )

    args = parser.parse_args()

    config = load_config()

    if args.audio_test:
        await run_audio_test(config)
        return

    app = Application(config)

    try:
        await app.start()

        while True:
            await asyncio.sleep(1)

    finally:
        await app.stop()


if __name__ == "__main__":
    try:
        asyncio.run(async_main())

    except KeyboardInterrupt:
        pass