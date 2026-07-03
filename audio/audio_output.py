from abc import ABC
from abc import abstractmethod


class AudioOutput(ABC):

    async def start(self):
        pass

    async def stop(self):
        pass

    @abstractmethod
    async def output(self, wav: bytes):
        pass