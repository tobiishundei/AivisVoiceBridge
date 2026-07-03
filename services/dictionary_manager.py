"""
読み上げ用辞書の読み込みと文字列置換を行う。

辞書は以下の順番で読み込む。

1. dictionaries/common
2. dictionaries/game/<game_dictionary>
3. dictionaries/personal

後から読み込まれた辞書が同じキーを上書きするため、
personal 辞書が最も優先される。
"""

import json
import re
import unicodedata
from pathlib import Path


COMMON_DICTIONARY_DIR = Path("dictionaries/common")
GAME_DICTIONARY_DIR = Path("dictionaries/game")
PERSONAL_DICTIONARY_DIR = Path("dictionaries/personal")


class DictionaryManager:
    """
    辞書による正規化と置換を行うクラス。
    """

    def __init__(self):
        self.dictionary = {}

    def load(self, game_dictionary: str):
        """
        共通辞書、ゲーム辞書、個人辞書を読み込む。
        """

        self.dictionary.clear()

        self._load_directory(
            COMMON_DICTIONARY_DIR
        )

        self._load_directory(
            GAME_DICTIONARY_DIR / game_dictionary
        )

        self._load_directory(
            PERSONAL_DICTIONARY_DIR
        )

    def process(self, text: str) -> str:
        """
        テキストを正規化し、辞書置換を適用する。
        """

        text = self.normalize(text)
        text = self.replace(text)

        return text

    def normalize(self, text: str) -> str:
        """
        辞書置換前の簡易正規化を行う。
        """

        text = unicodedata.normalize(
            "NFKC",
            text,
        )

        text = self._normalize_laughter(text)
        text = self._normalize_clap(text)

        return text

    def replace(self, text: str) -> str:
        """
        読み込まれた辞書に従って文字列を置換する。
        """

        for before, after in self.dictionary.items():
            text = text.replace(
                before,
                after,
            )

        return text

    def _normalize_laughter(self, text: str) -> str:
        """
        wwwww のような連続した w を www にまとめる。
        """

        return re.sub(
            r"w{3,}",
            "www",
            text,
            flags=re.IGNORECASE,
        )

    def _normalize_clap(self, text: str) -> str:
        """
        88888 のような連続した 8 を 888 にまとめる。
        """

        return re.sub(
            r"8{3,}",
            "888",
            text,
        )

    def _load_directory(self, directory: Path):
        """
        指定ディレクトリ配下の JSON 辞書を読み込む。
        """

        if not directory.exists():
            return

        for file in sorted(directory.rglob("*.json")):
            self._load_file(file)

    def _load_file(self, file: Path):
        """
        JSON辞書ファイルを読み込み、現在の辞書へ反映する。
        """

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.dictionary.update(data)