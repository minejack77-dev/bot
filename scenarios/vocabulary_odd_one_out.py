from enum import Enum
from typing import Optional

class OddOneOutType(Enum):
    CIRCLE_DIFFERENT = "Circle the different word"
    CIRCLE_SOUND = "Circle the word with certain sound"

class DifferenceCriterion(Enum):
    SOUND = "Sound"
    MEANING = "Meaning"
    OTHER = "Other"

class VocabularyOddOneOut:
    def __init__(self):
        self.task_type: Optional[OddOneOutType] = None
        self.criterion: Optional[DifferenceCriterion] = None
        self.criterion_custom: Optional[str] = None
        self.sound: Optional[str] = None

    def set_task_type(self, task_type: OddOneOutType):
        self.task_type = task_type

    def set_criterion(self, criterion: DifferenceCriterion, custom: Optional[str] = None):
        self.criterion = criterion
        if criterion == DifferenceCriterion.OTHER:
            self.criterion_custom = custom

    def set_sound(self, sound: str):
        self.sound = sound

    def generate_instruction(self) -> str:
        if self.task_type == OddOneOutType.CIRCLE_DIFFERENT:
            criterion = self.criterion_custom if self.criterion == DifferenceCriterion.OTHER else self.criterion.value.lower()
            return f"Circle the word with a different {criterion}."
        elif self.task_type == OddOneOutType.CIRCLE_SOUND:
            return f"Circle one word in each group which ends in {self.sound}."
        else:
            return "" 