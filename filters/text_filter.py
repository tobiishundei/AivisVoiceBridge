"""
チャット本文に対する最終的なテキスト整形を行う。

Normalizer でURL、笑い、拍手、句読点などを整形したあと、
空白の整理と空メッセージ対策を行う。
"""

import re

from filters.normalizer import Normalizer
from models.chat_message import ChatMessage


SPACE_PATTERN = re.compile(
    r"\s+"
)


class TextFilter:
    """
    ChatMessage の text を読み上げ向けに整形するクラス。
    """

    def __init__(self):
        self.normalizer = Normalizer()

    def filter(
        self,
        message: ChatMessage,
    ) -> ChatMessage:
        """
        ChatMessage の本文を整形して返す。
        """

        text = message.text

        text = self.normalizer.normalize(text)
        text = self._normalize_space(text)
        text = self._fallback_empty_text(text)

        message.text = text

        return message

    def _normalize_space(self, text: str) -> str:
        """
        改行や連続スペースを1つの半角スペースにまとめる。
        """

        return SPACE_PATTERN.sub(
            " ",
            text,
        ).strip()

    def _fallback_empty_text(self, text: str) -> str:
        """
        空文字になった場合の読み上げ用テキストを返す。
        """

        if text == "":
            return "（空のメッセージ）"

        return text