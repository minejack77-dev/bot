from typing import Optional


class ReadingTrueFalse:
    def __init__(self):
        self.read_first: Optional[bool] = None

    def set_read_first(self, read_first: bool):
        self.read_first = read_first

    def generate_instruction(self) -> str:
        instruction = "Match the sentences T (true) or F (false)."
        if self.read_first:
            instruction = "Read the text. " + instruction
        return instruction