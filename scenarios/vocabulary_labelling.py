from enum import Enum
from typing import Optional, List


class LabelType(Enum):
    ACTIONS = "Actions (verbs)"
    PLACES = "Places/buildings"
    OBJECTS = "Objects/things"
    OTHER = "Other"


class TaskFormat(Enum):
    SIMPLE = "Just label the pictures"
    ING_FORM = "Label using the verb +ing form"


class WordListOption(Enum):
    WITH_LIST = "Yes"
    WITHOUT_LIST = "No"


class VocabularyLabelling:
    def __init__(self):
        self.label_type: Optional[LabelType] = None
        self.task_format: Optional[TaskFormat] = None
        self.word_list_option: Optional[WordListOption] = None
        self.custom_type: Optional[str] = None

    def set_label_type(self, label_type: LabelType, custom_type: str = None):
        self.label_type = label_type
        if label_type == LabelType.OTHER:
            self.custom_type = custom_type

    def set_task_format(self, task_format: TaskFormat):
        self.task_format = task_format

    def set_word_list_option(self, word_list_option: WordListOption):
        self.word_list_option = word_list_option

    def generate_instruction(self) -> str:
        if not all([self.label_type, self.task_format, self.word_list_option]):
            raise ValueError("Не все параметры задания установлены")

        base_instruction = "Label the "

        # Тип подписи
        if self.label_type == LabelType.ACTIONS:
            if self.task_format == TaskFormat.ING_FORM:
                base_instruction += "activities"
            else:
                base_instruction += "actions"
        elif self.label_type == LabelType.PLACES:
            base_instruction += "places/buildings"
        elif self.label_type == LabelType.OBJECTS:
            base_instruction += "objects"
        else:  # OTHER
            base_instruction += self.custom_type.lower()

        base_instruction += " in the pictures"

        # Нужен ли список слов
        if self.word_list_option == WordListOption.WITH_LIST:
            base_instruction += " using the words from the list"

        # Для глаголов +ing
        if self.label_type == LabelType.ACTIONS and self.task_format == TaskFormat.ING_FORM:
            base_instruction += " with the +ing form of the verbs"

        base_instruction += "."
        return base_instruction