from enum import Enum
from typing import Optional


class GrammarCompletionTextType(Enum):
    TEXT = "text"
    SENTENCES = "sentences"
    CONVERSATION = "conversation"
    OTHER = "other"


class GrammarCompletionTaskType(Enum):
    CORRECT_FORM = "Correct form of the verbs"
    CERTAIN_FORM = "Certain form of the verb"
    CHOOSE_TWO = "Choose one of two forms of the verb"
    PHRASES = "Phrases"
    OTHER = "Other"


class GrammarCompletionWhere(Enum):
    IN_BRACKETS = "in brackets"
    IN_BOX = "in the box"
    IN_LIST = "in the list"


class GrammarCompletion:
    def __init__(self):
        self.text_type: Optional[GrammarCompletionTextType] = None
        self.text_type_other: Optional[str] = None
        self.task_type: Optional[GrammarCompletionTaskType] = None
        self.tense: Optional[str] = None
        self.tense1: Optional[str] = None
        self.tense2: Optional[str] = None
        self.verbs_given: Optional[bool] = None
        self.phrases_given: Optional[bool] = None
        self.other_word: Optional[str] = None
        self.other_given: Optional[bool] = None
        self.where: Optional[GrammarCompletionWhere] = None

    def set_text_type(self, text_type: GrammarCompletionTextType, text_type_other: Optional[str] = None):
        self.text_type = text_type
        self.text_type_other = text_type_other

    def set_task_type(self, task_type: GrammarCompletionTaskType):
        self.task_type = task_type

    def set_tense(self, tense: str):
        self.tense = tense

    def set_tenses(self, tense1: str, tense2: Optional[str]):
        self.tense1, self.tense2 = tense1, tense2

    def set_verbs_given(self, verbs_given: bool):
        self.verbs_given = verbs_given

    def set_phrases_given(self, phrases_given: bool):
        self.phrases_given = phrases_given

    def set_other_word(self, word: str):
        self.other_word = word

    def set_other_given(self, given: bool):
        self.other_given = given

    def set_where(self, where: GrammarCompletionWhere):
        self.where = where

    def generate_instruction(self) -> str:
        if not self.text_type:
            return ""

        text_type = (
            self.text_type_other
            if self.text_type == GrammarCompletionTextType.OTHER
            else self.text_type.value
        )
        base = f"Complete the {text_type}"

        if self.task_type == GrammarCompletionTaskType.CORRECT_FORM:
            return f"{base} with the correct form of the verbs" + (f" {self.where.value}." if self.verbs_given else ".")
        elif self.task_type == GrammarCompletionTaskType.CERTAIN_FORM:
            return f"{base} with the {self.tense}."
        elif self.task_type == GrammarCompletionTaskType.CHOOSE_TWO:
            return f"{base} with the {self.tense1} or {self.tense2}."
        elif self.task_type == GrammarCompletionTaskType.PHRASES:
            return f"{base} with the phrases" + (f" {self.where.value}." if self.phrases_given else ".")
        elif self.task_type == GrammarCompletionTaskType.OTHER:
            return f"{base} with the {self.other_word}" + (f" {self.where.value}." if self.other_given else ".")
        return ""