from enum import Enum
from typing import Optional


class MatchingType(Enum):
    SENTENCES_TO_PICTURES = "Sentences to pictures"
    DESCRIPTIONS_TO_WORDS = "Descriptions to words"
    QUESTIONS_TO_ANSWERS = "Questions to answers"
    OTHER = "Other"


class WordType(Enum):
    WORDS = "Words"
    NOUNS = "Nouns"
    ADJECTIVES = "Adjectives"
    VERBS = "Verbs"
    OTHER = "Other"


class VocabularyMatching:
    def __init__(self):
        self.matching_type: Optional[MatchingType] = None
        self.sent_range: Optional[str] = None
        self.pic_range: Optional[str] = None
        self.desc_word_type: Optional[WordType] = None
        self.desc_word_type_custom: Optional[str] = None
        self.q_range: Optional[str] = None
        self.a_range: Optional[str] = None
        self.other_first: Optional[str] = None
        self.other_second: Optional[WordType] = None
        self.other_second_custom: Optional[str] = None

    def set_matching_type(self, matching_type: MatchingType):
        self.matching_type = matching_type

    def set_sentences_range(self, sent_range: str):
        self.sent_range = sent_range

    def set_pictures_range(self, pic_range: str):
        self.pic_range = pic_range

    def set_desc_word_type(self, word_type: WordType, custom: Optional[str] = None):
        self.desc_word_type = word_type
        if word_type == WordType.OTHER:
            self.desc_word_type_custom = custom

    def set_questions_range(self, q_range: str):
        self.q_range = q_range

    def set_answers_range(self, a_range: str):
        self.a_range = a_range

    def set_other_first(self, other_first: str):
        self.other_first = other_first

    def set_other_second(self, word_type: WordType, custom: Optional[str] = None):
        self.other_second = word_type
        if word_type == WordType.OTHER:
            self.other_second_custom = custom

    def generate_instruction(self) -> str:
        if not self.matching_type:
            raise ValueError("Matching type is not set")

        if self.matching_type == MatchingType.SENTENCES_TO_PICTURES:
            if not self.sent_range or not self.pic_range:
                raise ValueError("Sentence and picture ranges must be set")
            return f"Match sentences {self.sent_range} to pictures {self.pic_range}."

        elif self.matching_type == MatchingType.DESCRIPTIONS_TO_WORDS:
            if not self.desc_word_type:
                raise ValueError("Word type must be set for descriptions-to-words task")
            word_type = (
                self.desc_word_type_custom
                if self.desc_word_type == WordType.OTHER
                else self.desc_word_type.value.lower()
            )
            return f"Match the descriptions to the {word_type}."

        elif self.matching_type == MatchingType.QUESTIONS_TO_ANSWERS:
            if not self.q_range or not self.a_range:
                raise ValueError("Question and answer ranges must be set")
            return f"Match questions {self.q_range} to answers {self.a_range}."

        elif self.matching_type == MatchingType.OTHER:
            if not self.other_first or not self.other_second:
                raise ValueError("Both sides of matching must be set for 'Other' type")
            second = (
                self.other_second_custom
                if self.other_second == WordType.OTHER
                else self.other_second.value.lower()
            )
            return f"Match the {self.other_first} to the {second}."

        return ""