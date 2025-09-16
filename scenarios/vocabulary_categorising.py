from enum import Enum
from typing import Optional


class TaskType(Enum):
    FILL_TABLE = "Fill the table"


class TableType(Enum):
    COUNTRIES_NATIONALITIES = "Countries and nationalities"
    JUST_CHART = "Just a chart"
    OTHER = "Other"


class VocabularyCategorising:
    def __init__(self):
        self.task_type: Optional[TaskType] = None
        self.table_type: Optional[TableType] = None
        self.custom_type: Optional[str] = None

    def set_task_type(self, task_type: TaskType):
        self.task_type = task_type

    def set_table_type(self, table_type: TableType, custom_type: Optional[str] = None):
        self.table_type = table_type
        if table_type == TableType.OTHER:
            self.custom_type = custom_type

    def generate_instruction(self) -> str:
        if not self.task_type or not self.table_type:
            raise ValueError("Не все параметры задания установлены")

        base_instruction = "Complete the chart"

        if self.table_type == TableType.COUNTRIES_NATIONALITIES:
            base_instruction += f" with {self.table_type.value.lower()}"
        elif self.table_type == TableType.JUST_CHART:
            base_instruction += "."
            return base_instruction
        elif self.table_type == TableType.OTHER:
            base_instruction += f" with {self.custom_type.lower()}"

        base_instruction += "."
        return base_instruction