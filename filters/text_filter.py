import re

from filters.normalizer import Normalizer
from models.chat_message import ChatMessage


class TextFilter:

    SPACE_PATTERN = re.compile(
        r"\s+"
    )

    def __init__(self):

        self.normalizer = Normalizer()

    def filter(
        self,
        message: ChatMessage
    ) -> ChatMessage:

        text = message.text

        #
        # 正規化
        #
        text = self.normalizer.normalize(text)

        #
        # 改行・連続スペース
        #
        text = self.SPACE_PATTERN.sub(
            " ",
            text
        ).strip()

        #
        # 空文字対策
        #
        if text == "":
            text = "（空のメッセージ）"

        message.text = text

        return message