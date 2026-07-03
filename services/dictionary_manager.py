import json
import re
import unicodedata
from pathlib import Path


class DictionaryManager:

    def __init__(self):

        self.dictionary = {}

    def load(
        self,
        game_dictionary: str
    ):

        self.dictionary.clear()

        #
        # 共通辞書
        #
        self._load_directory(
            Path("dictionaries/common")
        )

        #
        # ゲーム辞書
        #
        self._load_directory(
            Path("dictionaries/game")
            / game_dictionary
        )

        #
        # 個人辞書
        #
        self._load_directory(
            Path("dictionaries/personal")
        )
    
    def process(self, text: str) -> str:

        text = self.normalize(text)

        text = self.replace(text)

        return text

    def normalize(self, text: str) -> str:

        #
        # 全角→半角
        #
        text = unicodedata.normalize(
            "NFKC",
            text
        )

        #
        # WWWWWW → www
        #
        text = re.sub(
            r"w{3,}",
            "www",
            text,
            flags=re.IGNORECASE
        )

        #
        # 888888 → 888
        #
        text = re.sub(
            r"8{3,}",
            "888",
            text
        )

        return text

    def replace(self, text: str) -> str:

        for before, after in self.dictionary.items():

            text = text.replace(
                before,
                after
            )

        return text

    def _load_directory(self, directory: Path):

        if not directory.exists():
            return

        for file in sorted(directory.rglob("*.json")):

            with open(file, "r", encoding="utf-8") as f:

                data = json.load(f)

                self.dictionary.update(data)