import re


class UrlRule:

    URL_PATTERN = re.compile(
        r"https?://\S+"
    )

    def apply(self, text: str) -> str:

        return self.URL_PATTERN.sub(
            "URL省略",
            text
        )