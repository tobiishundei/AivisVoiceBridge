"""
連続する w / W を読み上げ向けの笑い表現に置き換えるルール。

例:
    wwwww
    WWWWW

これらを `ワラワラ` に変換する。
"""

import re


LAUGHTER_PATTERN = re.compile(
    r"w{3,}",
    re.IGNORECASE,
)

LAUGHTER_REPLACEMENT = "ワラワラ"


class LaughterRule:
    """
    連続する w を笑い表現へ置き換える正規化ルール。
    """

    def apply(self, text: str) -> str:
        """
        テキスト内の連続した w / W を `ワラワラ` に置き換える。
        """

        return LAUGHTER_PATTERN.sub(
            LAUGHTER_REPLACEMENT,
            text,
        )