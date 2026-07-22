"""
常駐音声プレイヤーを管理する音声出力バックエンド。

Tkinterとsounddeviceは専用の子プロセスで動作させ、
親プロセスとはmultiprocessing.Queueで通信する。
"""

import asyncio
import multiprocessing
import queue
import uuid

from audio.audio_output import AudioOutput
from audio.persistent_player import run_persistent_player


class PersistentAudioOutput(AudioOutput):
    """
    常駐音声プレイヤーの子プロセスを管理する。
    """

    START_TIMEOUT = 10.0
    STOP_TIMEOUT = 5.0

    def __init__(
        self,
        app_name: str,
        logger=None,
    ):
        self.app_name = app_name
        self.logger = logger

        self._context = multiprocessing.get_context(
            "spawn"
        )

        self._command_queue = None
        self._event_queue = None
        self._process = None

        self._started = False
        self._output_lock = asyncio.Lock()

    def _info(self, message: str):
        if self.logger:
            self.logger.info(message)
        else:
            print(message)

    def _error(self, message: str):
        if self.logger:
            self.logger.error(message)
        else:
            print(message)

    async def start(self):
        """
        常駐音声プレイヤーの子プロセスを開始する。
        """
        if self._started:
            return

        self._command_queue = (
            self._context.Queue()
        )

        self._event_queue = (
            self._context.Queue()
        )

        self._process = self._context.Process(
            target=run_persistent_player,
            args=(
                self._command_queue,
                self._event_queue,
                self.app_name,
            ),
            name="AivisVoiceBridgeAudioPlayer",
        )

        self._process.start()

        try:
            event = await asyncio.wait_for(
                asyncio.to_thread(
                    self._event_queue.get
                ),
                timeout=self.START_TIMEOUT,
            )

        except TimeoutError:
            await self._terminate_process()

            raise RuntimeError(
                "常駐音声プレイヤーの起動が"
                "タイムアウトしました。"
            )

        if event.get("type") == "error":
            await self._terminate_process()

            raise RuntimeError(
                "常駐音声プレイヤーの起動に"
                "失敗しました: "
                f"{event.get('message', '')}"
            )

        if event.get("type") != "ready":
            await self._terminate_process()

            raise RuntimeError(
                "常駐音声プレイヤーから"
                "不明な起動応答を受信しました。"
            )

        self._started = True

        self._info(
            "PersistentAudioOutput started: "
            f"{event.get('device', 'unknown')}"
        )

    async def stop(self):
        """
        常駐音声プレイヤーの子プロセスを終了する。
        """
        if not self._started:
            return

        self._started = False

        if (
            self._process is not None
            and self._process.is_alive()
        ):
            self._command_queue.put({
                "type": "stop",
            })

            await asyncio.to_thread(
                self._process.join,
                self.STOP_TIMEOUT,
            )

        if (
            self._process is not None
            and self._process.is_alive()
        ):
            self._process.terminate()

            await asyncio.to_thread(
                self._process.join,
                self.STOP_TIMEOUT,
            )

        self._close_queues()

        self._process = None

        self._info(
            "PersistentAudioOutput stopped"
        )

    async def output(self, wav: bytes):
        """
        WAVデータを子プロセスへ送り、
        再生完了まで待機する。
        """
        if not self._started:
            raise RuntimeError(
                "PersistentAudioOutput is not started"
            )

        async with self._output_lock:
            item_id = uuid.uuid4().hex

            self._command_queue.put({
                "type": "play",
                "id": item_id,
                "wav": wav,
            })

            while True:
                if (
                    self._process is None
                    or not self._process.is_alive()
                ):
                    raise RuntimeError(
                        "常駐音声プレイヤーが"
                        "予期せず終了しました。"
                    )

                try:
                    event = await asyncio.to_thread(
                        self._event_queue.get,
                        True,
                        0.5,
                    )

                except queue.Empty:
                    continue

                event_type = event.get(
                    "type"
                )

                if (
                    event_type == "completed"
                    and event.get("id") == item_id
                ):
                    return

                if (
                    event_type == "playback_error"
                    and event.get("id") == item_id
                ):
                    raise RuntimeError(
                        "音声再生に失敗しました: "
                        f"{event.get('message', '')}"
                    )

                if event_type == "error":
                    raise RuntimeError(
                        "常駐音声プレイヤーで"
                        "エラーが発生しました: "
                        f"{event.get('message', '')}"
                    )

    async def _terminate_process(self):
        """
        起動に失敗した子プロセスを終了する。
        """
        if (
            self._process is not None
            and self._process.is_alive()
        ):
            self._process.terminate()

            await asyncio.to_thread(
                self._process.join,
                self.STOP_TIMEOUT,
            )

        self._close_queues()
        self._process = None

    def _close_queues(self):
        """
        multiprocessing.Queueを閉じる。
        """
        for process_queue in (
            self._command_queue,
            self._event_queue,
        ):
            if process_queue is None:
                continue

            process_queue.close()
            process_queue.join_thread()

        self._command_queue = None
        self._event_queue = None
