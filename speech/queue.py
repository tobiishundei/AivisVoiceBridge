import asyncio

from models.chat_message import ChatMessage


class SpeechQueue:

    def __init__(self):
        self._queue: asyncio.Queue[ChatMessage] = asyncio.Queue()

    async def put(self, message: ChatMessage):
        await self._queue.put(message)

    async def get(self) -> ChatMessage:
        return await self._queue.get()

    def task_done(self):
        self._queue.task_done()

    def empty(self) -> bool:
        return self._queue.empty()

    def size(self) -> int:
        return self._queue.qsize()