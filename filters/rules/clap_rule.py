import re


class ClapRule:

    EIGHT_PATTERN = re.compile(
        r"8{4,}"
    )

    def apply(self, text: str) -> str:

        return self.EIGHT_PATTERN.sub(
            "パチパチ",
            text
        )