"""
連続する句読点・記号を読み上げ向けに整えるルール。

例:
    !!!!
    ？？？？
    ーーーー

これらを読み上げやすい長さにまとめる。
"""

import re


EXCLAMATION_PATTERN = re.compile(
    r"!{2,}|！{2,}"
)

QUESTION_PATTERN = re.compile(
    r"\?{2,}|？{2,}"
)

LONG_VOWEL_PATTERN = re.compile(
    r"ー{2,}"
)


class PunctuationRule:
    """
    連続した感嘆符、疑問符、長音記号を短くまとめる正規化ルール。
    """

    def apply(self, text: str) -> str:
        """
        テキスト内の連続記号を読み上げやすい形に整える。
        """

        text = EXCLAMATION_PATTERN.sub(
            "！",
            text,
        )

        text = QUESTION_PATTERN.sub(
            "？",
            text,
        )

        text = LONG_VOWEL_PATTERN.sub(
            "ー",
            text,
        )

        return text