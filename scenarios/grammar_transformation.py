from enum import Enum
from typing import Optional


class GrammarTransformationType(Enum):
    OPPOSITE_ADJECTIVE = "Opposite adjective"
    CHANGE_TENSE = "Change tense"


class GrammarTransformation:
    def __init__(self):
        self.transformation_type: Optional[GrammarTransformationType] = None
        self.tense1: Optional[str] = None
        self.tense2: Optional[str] = None

    def set_transformation_type(self, transformation_type: GrammarTransformationType):
        self.transformation_type = transformation_type

    def set_tense1(self, tense1: str):
        self.tense1 = tense1

    def set_tense2(self, tense2: str):
        self.tense2 = tense2

    def generate_instruction(self) -> str:
        if self.transformation_type == GrammarTransformationType.OPPOSITE_ADJECTIVE:
            return "Rewrite the sentences using the opposite adjective."
        if self.transformation_type == GrammarTransformationType.CHANGE_TENSE:
            return f"Change the sentences from the {self.tense1} to the {self.tense2}."
        return ""