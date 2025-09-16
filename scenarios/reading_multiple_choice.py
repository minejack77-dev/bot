from enum import Enum
from typing import Optional


class ReadingTextType(Enum):
    TEXT = "text"
    STORY = "story"
    DIALOGUE = "dialogue"
    OTHER = "other"


class ReadingMultipleChoice:
    def __init__(self):
        self.text_type: Optional[ReadingTextType] = None
        self.text_type_other: Optional[str] = None

    def set_text_type(self, text_type: ReadingTextType, text_type_other: Optional[str] = None):
        self.text_type = text_type
        self.text_type_other = text_type_other

    def generate_instruction(self) -> str:
        text_type = (
            self.text_type_other
            if self.text_type == ReadingTextType.OTHER
            else (self.text_type.value if self.text_type else "text")
        )
        return f"Read the {text_type}. Circle a, b, or c."