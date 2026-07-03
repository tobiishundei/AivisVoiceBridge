"""
読み上げ可否を判定するポリシー。

コメント内容やユーザーの連投状況を見て、
読み上げるかどうかと、スキップ理由を返す。
"""

import time

from services.skip_reason import SkipReason


class SpeechPolicy:
    """
    チャットメッセージを読み上げ対象にするか判定するクラス。
    """

    def __init__(self, config):
        self.max_length = config.max_length
        self.cooldown = config.cooldown
        self.skip_url_only = config.skip_url_only
        self.skip_empty = config.skip_empty

        self.last_user = None
        self.last_time = 0.0

    def should_read(self, message):
        """
        メッセージを読み上げるか判定する。

        Returns:
            tuple[bool, str]:
                1つ目は読み上げるかどうか。
                2つ目は SkipReason の文字列。
        """

        if self._is_empty(message):
            return False, SkipReason.EMPTY

        if self._is_too_long(message):
            return False, SkipReason.TOO_LONG

        if self._is_url_only(message):
            return False, SkipReason.URL_ONLY

        if self._is_in_cooldown(message):
            return False, SkipReason.COOLDOWN

        self._mark_as_spoken(message)

        return True, SkipReason.OK

    def _is_empty(self, message) -> bool:
        """
        空メッセージか判定する。
        """

        return (
            self.skip_empty
            and not message.text.strip()
        )

    def _is_too_long(self, message) -> bool:
        """
        最大文字数を超えているか判定する。
        """

        return len(message.text) > self.max_length

    def _is_url_only(self, message) -> bool:
        """
        URLのみのメッセージか判定する。

        TextFilter によりURLのみのメッセージは "URL省略" に正規化される。
        """

        return (
            self.skip_url_only
            and message.text == "URL省略"
        )

    def _is_in_cooldown(self, message) -> bool:
        """
        同一ユーザーの連続読み上げ制限に該当するか判定する。
        """

        now = time.time()

        return (
            self.last_user == message.user_id
            and now - self.last_time < self.cooldown
        )

    def _mark_as_spoken(self, message):
        """
        最後に読み上げたユーザーと時刻を記録する。
        """

        self.last_user = message.user_id
        self.last_time = time.time()