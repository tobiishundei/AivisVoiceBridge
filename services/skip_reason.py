"""
読み上げをスキップした理由を表す定数。

SpeechPolicy は、読み上げ可否とあわせて SkipReason を返す。
ログやデバッグで「なぜ読まれなかったか」を確認するために使う。
"""


class SkipReason:
    """
    読み上げスキップ理由の文字列定数。
    """

    OK = "ok"

    EMPTY = "empty"
    URL_ONLY = "url_only"
    TOO_LONG = "too_long"
    COOLDOWN = "cooldown"

    NG_WORD = "ng_word"
    COMMAND = "command"
    EMOTE_ONLY = "emote_only"
    BROADCASTER_ONLY = "broadcaster_only"