from enum import Enum


class GivenType(Enum):
    PHRASES = "Phrases"
    QUESTIONS = "Questions"
    OTHER = "Other"


class PrepInfo(Enum):
    NONE = "None"
    TEXT = "Text"
    AUDIO = "Audio"
    PICTURE = "Picture"


class GrammarErrorCorrection:
    def __init__(self):
        self.given_type: GivenType | str | None = None
        self.need_correction: bool | None = None
        self.prep_info: PrepInfo | None = None
        self.prep_info_type: str | None = None
        self.prep_info_clarify: str | None = None

    def set_given_type(self, given_type: GivenType, custom: str = None):
        if given_type == GivenType.OTHER and custom:
            self.given_type = custom
        else:
            self.given_type = given_type

    def set_need_correction(self, need_correction: bool):
        self.need_correction = need_correction

    def set_prep_info(self, prep_info: PrepInfo):
        self.prep_info = prep_info

    def set_prep_info_type(self, prep_info_type: str):
        self.prep_info_type = prep_info_type

    def set_prep_info_clarify(self, prep_info_clarify: str):
        self.prep_info_clarify = prep_info_clarify

    def generate_instruction(self) -> str:
        type_str = self.given_type if isinstance(self.given_type, str) else self.given_type.value.lower()

        if self.prep_info == PrepInfo.NONE:
            if not self.need_correction:
                return f"Are the {type_str} right (✓) or wrong (✗)?"
            else:
                return f"Are the {type_str} right (✓) or wrong (✗)? Correct the wrong {type_str}."

        action_map = {
            PrepInfo.TEXT: "Read the",
            PrepInfo.AUDIO: "Listen to the",
            PrepInfo.PICTURE: "Look at the",
        }
        action = action_map.get(self.prep_info, "Look at the")
        info = (self.prep_info_clarify or self.prep_info_type or "").lower()

        if not self.need_correction:
            return f"{action} {info}. Are the {type_str} right (✓) or wrong (✗)?"
        else:
            return f"{action} {info}. Are the {type_str} right (✓) or wrong (✗)? Correct the wrong {type_str}."