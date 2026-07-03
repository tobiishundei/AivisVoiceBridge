"""
URLを読み上げ向けの省略表現に置き換えるルール。

URL本文をそのまま読み上げると長くなりやすいため、
`URL省略` に変換する。
"""

import re


URL_PATTERN = re.compile(
    r"https?://\S+"
)

URL_REPLACEMENT = "URL省略"


class UrlRule:
    """
    URLを `URL省略` に置き換える正規化ルール。
    """

    def apply(self, text: str) -> str:
        """
        テキスト内のURLを省略表現へ置き換える。
        """

        return URL_PATTERN.sub(
            URL_REPLACEMENT,
            text,
        )