"""
連続する 8 を読み上げ向けの拍手表現に置き換えるルール。

例:
    8888
    88888888

これらを `パチパチパチパチ` に変換する。
"""

import re


CLAP_PATTERN = re.compile(
    r"8{4,}"
)

CLAP_REPLACEMENT = "パチパチパチパチ"


class ClapRule:
    """
    連続する 8 を拍手表現へ置き換える正規化ルール。
    """

    def apply(self, text: str) -> str:
        """
        テキスト内の連続した 8 を `パチパチパチパチ` に置き換える。
        """

        return CLAP_PATTERN.sub(
            CLAP_REPLACEMENT,
            text,
        )