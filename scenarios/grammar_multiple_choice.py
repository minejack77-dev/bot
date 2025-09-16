from enum import Enum
from typing import Optional


class GrammarMultipleChoiceType(Enum):
    CIRCLE_CORRECT = "Circle the correct one"
    OTHER = "Other"


class GrammarMultipleChoiceSubject(Enum):
    WORD = "word"
    VERB = "verb"
    ANSWER = "answer"
    OTHER = "other"


class GrammarMultipleChoice:
    def __init__(self):
        self.task_type: Optional[GrammarMultipleChoiceType] = None
        self.subject: Optional[GrammarMultipleChoiceSubject] = None
        self.subject_other: Optional[str] = None

    def set_task_type(self, task_type: GrammarMultipleChoiceType):
        self.task_type = task_type

    def set_subject(self, subject: GrammarMultipleChoiceSubject, subject_other: Optional[str] = None):
        self.subject = subject
        self.subject_other = subject_other

    def generate_instruction(self) -> str:
        if not self.subject:
            return ""

        subj = (
            self.subject_other
            if self.subject == GrammarMultipleChoiceSubject.OTHER
            else self.subject.value
        )
        return f"Circle the correct {subj}."