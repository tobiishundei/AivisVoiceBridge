"""
読み上げ前テキストの正規化ルールを順番に適用する。

URL、省略表現、笑い、拍手、句読点などの整形は、
個別の rule クラスに分けて管理する。
"""

from filters.rules.clap_rule import ClapRule
from filters.rules.laughter_rule import LaughterRule
from filters.rules.punctuation_rule import PunctuationRule
from filters.rules.url_rule import UrlRule


class Normalizer:
    """
    複数の正規化ルールを順番に適用するクラス。
    """

    def __init__(self):
        self.rules = [
            UrlRule(),
            LaughterRule(),
            ClapRule(),
            PunctuationRule(),
        ]

    def normalize(
        self,
        text: str,
    ) -> str:
        """
        登録されたルールを順番に適用して、正規化済みテキストを返す。
        """

        for rule in self.rules:
            text = rule.apply(text)

        return text