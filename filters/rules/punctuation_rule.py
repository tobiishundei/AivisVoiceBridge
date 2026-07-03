import re


class PunctuationRule:

    EXCLAMATION_PATTERN = re.compile(r"!{2,}|！{2,}")
    QUESTION_PATTERN = re.compile(r"\?{2,}|？{2,}")
    LONG_PATTERN = re.compile(r"ー{2,}")

    def apply(self, text: str) -> str:

        #
        # !!!!!!!
        #
        text = self.EXCLAMATION_PATTERN.sub(
            "！",
            text
        )

        #
        # ???????
        #
        text = self.QUESTION_PATTERN.sub(
            "？",
            text
        )

        #
        # ーーーーーー
        #
        text = self.LONG_PATTERN.sub(
            "ー",
            text
        )

        return text