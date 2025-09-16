from enum import Enum
from typing import Optional


class SynonymsTaskType(Enum):
    CHOOSE_POS = "Choose part of speech out of two"
    OPP_SIM_ADJ = "Opposite/similar adjectives"


class PartOfSpeech(Enum):
    NOUNS = "Nouns"
    PRONOUNS = "Pronouns"
    ADJECTIVES = "Adjectives"
    VERBS = "Verbs"
    ADVERBS = "Adverbs"
    OTHER = "Other"


class AdjectiveType(Enum):
    OPPOSITE = "Opposite"
    SIMILAR = "Similar"


class VocabularySynonyms:
    def __init__(self):
        self.task_type: Optional[SynonymsTaskType] = None
        self.pos1: Optional[PartOfSpeech] = None
        self.pos1_custom: Optional[str] = None
        self.pos2: Optional[PartOfSpeech] = None
        self.pos2_custom: Optional[str] = None
        self.adj_type: Optional[AdjectiveType] = None

    def set_task_type(self, task_type: SynonymsTaskType):
        self.task_type = task_type

    def set_pos1(self, pos: PartOfSpeech, custom: Optional[str] = None):
        self.pos1 = pos
        if pos == PartOfSpeech.OTHER:
            custom_norm = (custom or "").strip()
            if not custom_norm:
                raise ValueError("For pos1=OTHER you must provide a non-empty custom value")
            self.pos1_custom = custom_norm
        else:
            self.pos1_custom = None

    def set_pos2(self, pos: PartOfSpeech, custom: Optional[str] = None):
        self.pos2 = pos
        if pos == PartOfSpeech.OTHER:
            custom_norm = (custom or "").strip()
            if not custom_norm:
                raise ValueError("For pos2=OTHER you must provide a non-empty custom value")
            self.pos2_custom = custom_norm
        else:
            self.pos2_custom = None

    def set_adj_type(self, adj_type: AdjectiveType):
        self.adj_type = adj_type

    def generate_instruction(self) -> str:
        if not self.task_type:
            raise ValueError("Task type is not set")

        if self.task_type == SynonymsTaskType.CHOOSE_POS:
            if not self.pos1 or not self.pos2:
                raise ValueError("Both parts of speech must be set for CHOOSE_POS task")
            pos1 = self.pos1_custom if self.pos1 == PartOfSpeech.OTHER else self.pos1.value.lower()
            pos2 = self.pos2_custom if self.pos2 == PartOfSpeech.OTHER else self.pos2.value.lower()
            return f"Are the words in bold {pos1} or {pos2}?"

        if self.task_type == SynonymsTaskType.OPP_SIM_ADJ:
            if not self.adj_type:
                raise ValueError("Adjective type must be set for OPP_SIM_ADJ task")
            return f"Write the {self.adj_type.value.lower()} adjectives."

        return ""