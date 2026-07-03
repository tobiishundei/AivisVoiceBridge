import time

from services.skip_reason import SkipReason


class SpeechPolicy:

    def __init__(self, config):

        #
        # 前回読み上げ情報
        #
        self.last_user = None
        self.last_time = 0

        #
        # 設定
        #
        self.max_length = config.max_length
        self.cooldown = config.cooldown

        self.skip_url_only = config.skip_url_only
        self.skip_empty = config.skip_empty

    def should_read(self, message):

        #
        # 空メッセージ
        #
        if (
            self.skip_empty
            and
            not message.text.strip()
        ):
            return False, SkipReason.EMPTY

        #
        # 長文
        #
        if len(message.text) > self.max_length:
            return False, SkipReason.TOO_LONG

        #
        # URLのみ
        #
        if (
            self.skip_url_only
            and
            message.text == "URL省略"
        ):
            return False, SkipReason.URL_ONLY

        #
        # 同一ユーザーの連投
        #
        now = time.time()

        if (
            self.last_user == message.user_id
            and
            now - self.last_time < self.cooldown
        ):
            return False, SkipReason.COOLDOWN

        #
        # 最終読み上げ情報を更新
        #
        self.last_user = message.user_id
        self.last_time = now

        return True, SkipReason.OK