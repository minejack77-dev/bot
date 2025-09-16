from enum import Enum
from typing import Optional


class WordBuildingType(Enum):
    MISSING_LETTERS = "Missing letters"
    WORDS_FROM_LETTERS = "Words from letters"
    FORMS_OF_WORDS = "Forms of words"


class WordType(Enum):
    WORDS = "Words"
    ADJECTIVES = "Adjectives"
    NOUNS = "Nouns"
    VERBS = "Verbs"
    OTHER = "Other"


class MissingType(Enum):
    LETTERS = "Letters"
    VOWELS = "Vowels"
    CONSONANTS = "Consonants"


class VocabularyWordBuilding:
    def __init__(self):
        self.task_type: Optional[WordBuildingType] = None

        # Missing letters
        self.word_type: Optional[WordType] = None
        self.word_type_custom: Optional[str] = None
        self.missing_type: Optional[MissingType] = None

        # Forms of words
        self.build_type: Optional[WordType] = None
        self.build_type_custom: Optional[str] = None
        self.given_type: Optional[WordType] = None
        self.given_type_custom: Optional[str] = None

    def set_task_type(self, task_type: WordBuildingType):
        self.task_type = task_type

    def set_word_type(self, word_type: WordType, custom: Optional[str] = None):
        self.word_type = word_type
        if word_type == WordType.OTHER:
            custom_norm = (custom or "").strip()
            if not custom_norm:
                raise ValueError("For word_type=OTHER you must provide a non-empty custom value")
            self.word_type_custom = custom_norm
        else:
            self.word_type_custom = None

    def set_missing_type(self, missing_type: MissingType):
        self.missing_type = missing_type

    def set_build_type(self, build_type: WordType, custom: Optional[str] = None):
        self.build_type = build_type
        if build_type == WordType.OTHER:
            custom_norm = (custom or "").strip()
            if not custom_norm:
                raise ValueError("For build_type=OTHER you must provide a non-empty custom value")
            self.build_type_custom = custom_norm
        else:
            self.build_type_custom = None

    def set_given_type(self, given_type: WordType, custom: Optional[str] = None):
        self.given_type = given_type
        if given_type == WordType.OTHER:
            custom_norm = (custom or "").strip()
            if not custom_norm:
                raise ValueError("For given_type=OTHER you must provide a non-empty custom value")
            self.given_type_custom = custom_norm
        else:
            self.given_type_custom = None

    def generate_instruction(self) -> str:
        if not self.task_type:
            raise ValueError("Task type is not set")

        if self.task_type == WordBuildingType.MISSING_LETTERS:
            if not self.word_type or not self.missing_type:
                raise ValueError("word_type and missing_type must be set for MISSING_LETTERS")
            word_type = (
                self.word_type_custom
                if self.word_type == WordType.OTHER
                else self.word_type.value.lower()
            )
            missing = self.missing_type.value.lower()
            return f"Complete the {word_type} with the missing {missing}."

        if self.task_type == WordBuildingType.WORDS_FROM_LETTERS:
            if not self.word_type:
                raise ValueError("word_type must be set for WORDS_FROM_LETTERS")
            build_type = (
                self.word_type_custom
                if self.word_type == WordType.OTHER
                else self.word_type.value.lower()
            )
            return f"Build {build_type} from the letters."

        if self.task_type == WordBuildingType.FORMS_OF_WORDS:
            if not self.build_type or not self.given_type:
                raise ValueError("build_type and given_type must be set for FORMS_OF_WORDS")
            build_type = (
                self.build_type_custom
                if self.build_type == WordType.OTHER
                else self.build_type.value.lower()
            )
            given_type = (
                self.given_type_custom
                if self.given_type == WordType.OTHER
                else self.given_type.value.lower()
            )
            return f"Make {build_type} from {given_type} in the list."

        return ""