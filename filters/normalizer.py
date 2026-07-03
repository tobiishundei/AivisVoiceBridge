from filters.rules.url_rule import UrlRule
from filters.rules.laughter_rule import LaughterRule
from filters.rules.clap_rule import ClapRule
from filters.rules.punctuation_rule import PunctuationRule

class Normalizer:

    def __init__(self):

        self.rules = [

            UrlRule(),

            LaughterRule(),

            ClapRule(),

            PunctuationRule(),

        ]
        
    def normalize(
        self,
        text: str
    ) -> str:

        for rule in self.rules:

            text = rule.apply(text)

        return text