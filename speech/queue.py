"""
読み上げ待ちメッセージのキューを管理する。

TwitchClient / ChatHandler 側で受け取った ChatMessage をキューに積み、
SpeechWorker が順番に取り出して読み上げる。
"""

import asyncio

from models.chat_message import ChatMessage


class SpeechQueue:
    """
    ChatMessage 専用の非同期キュー。
    """

    def __init__(self):
        self._queue: asyncio.Queue[ChatMessage] = asyncio.Queue()

    async def put(self, message: ChatMessage):
        """
        読み上げ待ちメッセージをキューへ追加する。
        """

        await self._queue.put(message)

    async def get(self) -> ChatMessage:
        """
        次に読み上げるメッセージをキューから取り出す。
        """

        return await self._queue.get()

    def task_done(self):
        """
        取り出したメッセージの処理完了を通知する。
        """

        self._queue.task_done()

    def empty(self) -> bool:
        """
        キューが空かどうかを返す。
        """

        return self._queue.empty()

    def size(self) -> int:
        """
        現在キューに積まれているメッセージ数を返す。
        """

        return self._queue.qsize()