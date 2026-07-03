import re


class LaughterRule:

    WWW_PATTERN = re.compile(
        r"w{3,}",
        re.IGNORECASE
    )

    def apply(self, text: str) -> str:

        return self.WWW_PATTERN.sub(
            "ワラワラ",
            text
        )