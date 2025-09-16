from __future__ import annotations

from typing import Dict, Any, Optional


class CreateTaskFormulation:
    def __init__(self):
        # Единый сторедж состояний по chat_id
        self.sessions: Dict[int, Dict[str, Any]] = {}

    # ---------- helpers ----------
    def reset_session(self, chat_id: int, task_type: str | None = None):
        self.sessions[chat_id] = {
            "task_type": task_type,
            "state": None,
            # Сюда мы будем класть инстансы сценариев (по одному на блок)
            "labelling": None,
            "categorising": None,
            "word_building": None,
            "matching": None,
            "odd_one_out": None,
            "synonyms": None,
            "grammar_mc": None,
            "grammar_completion": None,
            "grammar_transformation": None,
            "grammar_error_correction": None,
            "reading_mc": None,
            "reading_tf": None,
        }

    def _s(self, chat_id: int) -> dict:
        if chat_id not in self.sessions:
            self.reset_session(chat_id)
        return self.sessions[chat_id]

    def get_state(self, chat_id: int) -> Optional[str]:
        """Возвращает текущее состояние (для роутера aiogram)."""
        return self._s(chat_id).get("state")

    def set_task_type(self, chat_id: int, section: str | None):
        """Сохраняет текущий раздел: vocabulary / grammar / reading (используется на экране 'done')."""
        self._s(chat_id)["task_type"] = section.lower() if section else None

    def _ask(self, chat_id: int, new_state: str, text: str, options: list[str] | None = None) -> Dict[str, Any]:
        self._s(chat_id)["state"] = new_state
        resp: Dict[str, Any] = {"text": text}
        if options:
            resp["options"] = [str(o) for o in options]
        return resp

    def _finish(self, chat_id: int, instruction: str) -> Dict[str, Any]:
        sess = self._s(chat_id)
        sess["state"] = None
        # очищаем инстансы сценариев
        for key in (
            "labelling", "categorising", "word_building", "matching", "odd_one_out",
            "synonyms", "grammar_mc", "grammar_completion", "grammar_transformation",
            "grammar_error_correction", "reading_mc", "reading_tf"
        ):
            sess[key] = None
        return {"text": f"Task formulation:\n{instruction}", "action": "done"}

    # ====== ИМПОРТЫ СЦЕНАРИЕВ (как атрибуты класса) ======
    # ---------- Vocabulary: Labelling ----------
    from scenarios.vocabulary_labelling import (
        VocabularyLabelling,
        LabelType,
        TaskFormat,
        WordListOption,
    )

    # ---------- Vocabulary: Categorising ----------
    from scenarios.vocabulary_categorising import VocabularyCategorising, TaskType, TableType

    # ---------- Vocabulary: Word-building ----------
    from scenarios.vocabulary_word_building import (
        VocabularyWordBuilding,
        WordBuildingType,
        WordType,
        MissingType,
    )

    # ---------- Vocabulary: Matching ----------
    from scenarios.vocabulary_matching import (
        VocabularyMatching,
        MatchingType,
        WordType as MatchingWordType,
    )

    # ---------- Vocabulary: Odd one out ----------
    from scenarios.vocabulary_odd_one_out import (
        VocabularyOddOneOut,
        OddOneOutType,
        DifferenceCriterion,
    )

    # ---------- Vocabulary: Synonyms / Antonyms ----------
    from scenarios.vocabulary_synonyms import (
        VocabularySynonyms,
        SynonymsTaskType,
        PartOfSpeech,
        AdjectiveType,
    )

    # ---------- Grammar: Multiple Choice ----------
    from scenarios.grammar_multiple_choice import (
        GrammarMultipleChoice,
        GrammarMultipleChoiceType,
        GrammarMultipleChoiceSubject,
    )

    # ---------- Grammar: Completion ----------
    from scenarios.grammar_completion import (
        GrammarCompletion,
        GrammarCompletionTextType,
        GrammarCompletionTaskType,
        GrammarCompletionWhere,
    )

    # ---------- Grammar: Transformation ----------
    from scenarios.grammar_transformation import GrammarTransformation, GrammarTransformationType

    # ---------- Grammar: Error Correction ----------
    from scenarios.grammar_error_correction import GrammarErrorCorrection, GivenType, PrepInfo

    # ---------- Reading: MC & T/F ----------
    from scenarios.reading_multiple_choice import ReadingMultipleChoice, ReadingTextType
    from scenarios.reading_true_false import ReadingTrueFalse

    # =======================
    #      LABELLING
    # =======================
    def start_labelling(self, chat_id: int):
        sess = self._s(chat_id)
        sess["labelling"] = self.VocabularyLabelling()
        return self._ask(
            chat_id,
            "labelling_label_type",
            "What do you want to label?",
            ["Actions (verbs)", "Places/buildings", "Objects/things", "Other", "Back to vocabulary"],
        )

    def labelling_label_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)

        if text == "Back to vocabulary":
            sess["state"] = None
            sess["labelling"] = None
            return {"action": "back_to_vocabulary"}

        type_map = {
            "Actions (verbs)": self.LabelType.ACTIONS,
            "Places/buildings": self.LabelType.PLACES,
            "Objects/things": self.LabelType.OBJECTS,
            "Other": self.LabelType.OTHER,
        }
        if text not in type_map:
            return {"text": "Please select one of the options."}

        if type_map[text] == self.LabelType.OTHER:
            return self._ask(chat_id, "labelling_label_type_other", "Please enter your own type:")

        sess["labelling"].set_label_type(type_map[text])
        return self._ask(
            chat_id,
            "labelling_task_format",
            "What is the format of the task?",
            ["Just label the pictures", "Label using the verb +ing form"],
        )

    def labelling_label_type_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty type (e.g., 'Food', 'Transportation')."}
        sess["labelling"].set_label_type(self.LabelType.OTHER, custom)
        return self._ask(
            chat_id,
            "labelling_task_format",
            "What is the format of the task?",
            ["Just label the pictures", "Label using the verb +ing form"],
        )

    def labelling_task_format(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        fmt_map = {
            "Just label the pictures": self.TaskFormat.SIMPLE,
            "Label using the verb +ing form": self.TaskFormat.ING_FORM,
        }
        if text not in fmt_map:
            return {"text": "Please select one of the options."}

        sess["labelling"].set_task_format(fmt_map[text])
        return self._ask(
            chat_id,
            "labelling_word_list_option",
            "Do you want to provide a word list for students?",
            ["Yes", "No"],
        )

    def labelling_word_list_option(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        opt_map = {"Yes": self.WordListOption.WITH_LIST, "No": self.WordListOption.WITHOUT_LIST}
        if text not in opt_map:
            return {"text": "Please select Yes or No."}

        sess["labelling"].set_word_list_option(opt_map[text])
        instruction = sess["labelling"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    #     CATEGORISING
    # =======================
    def start_categorising(self, chat_id: int):
        sess = self._s(chat_id)
        sess["categorising"] = self.VocabularyCategorising()
        return self._ask(
            chat_id,
            "categorising_task_type",
            "What type of categorising task do you want to create?",
            ["Fill the table", "Back to vocabulary"],
        )

    def categorising_task_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)

        if text == "Back to vocabulary":
            sess["state"] = None
            sess["categorising"] = None
            return {"action": "back_to_vocabulary"}

        if text != "Fill the table":
            return {"text": "Please select one of the options."}

        sess["categorising"].set_task_type(self.TaskType.FILL_TABLE)
        return self._ask(
            chat_id,
            "categorising_table_type",
            "What do you want students to complete in the table?",
            ["Countries and nationalities", "Just a chart", "Other"],
        )

    def categorising_table_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        type_map = {
            "Countries and nationalities": self.TableType.COUNTRIES_NATIONALITIES,
            "Just a chart": self.TableType.JUST_CHART,
        }

        if text == "Other":
            return self._ask(chat_id, "categorising_table_type_other", "Please enter your own type:")

        if text not in type_map:
            return {"text": "Please select one of the options."}

        sess["categorising"].set_table_type(type_map[text])
        instruction = sess["categorising"].generate_instruction()
        return self._finish(chat_id, instruction)

    def categorising_table_type_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty type."}
        sess["categorising"].set_table_type(self.TableType.OTHER, custom)
        instruction = sess["categorising"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    #    WORD-BUILDING
    # =======================
    def start_word_building(self, chat_id: int):
        sess = self._s(chat_id)
        sess["word_building"] = self.VocabularyWordBuilding()
        return self._ask(
            chat_id,
            "word_building_task_type",
            "What type of word-building task do you want to create?",
            ["Missing letters", "Words from letters", "Forms of words", "Back to vocabulary"],
        )

    def word_building_task_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)

        if text == "Back to vocabulary":
            sess["state"] = None
            sess["word_building"] = None
            return {"action": "back_to_vocabulary"}

        type_map = {
            "Missing letters": self.WordBuildingType.MISSING_LETTERS,
            "Words from letters": self.WordBuildingType.WORDS_FROM_LETTERS,
            "Forms of words": self.WordBuildingType.FORMS_OF_WORDS,
        }
        if text not in type_map:
            return {"text": "Please select one of the options."}

        sess["word_building"].set_task_type(type_map[text])

        if type_map[text] == self.WordBuildingType.MISSING_LETTERS:
            return self._ask(
                chat_id,
                "word_building_missing_word_type",
                "What type of words?",
                ["Words", "Adjectives", "Nouns", "Verbs", "Other"],
            )
        if type_map[text] == self.WordBuildingType.WORDS_FROM_LETTERS:
            return self._ask(
                chat_id,
                "word_building_words_from_letters_type",
                "What type of words should students build?",
                ["Words", "Nouns", "Verbs", "Adjectives", "Other"],
            )
        # FORMS_OF_WORDS
        return self._ask(
            chat_id,
            "word_building_forms_build_type",
            "What type of words should students build?",
            ["Words", "Nouns", "Verbs", "Adjectives", "Other"],
        )

    # --- Missing letters ---
    def word_building_missing_word_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        wt_map = {
            "Words": self.WordType.WORDS,
            "Adjectives": self.WordType.ADJECTIVES,
            "Nouns": self.WordType.NOUNS,
            "Verbs": self.WordType.VERBS,
            "Other": self.WordType.OTHER,
        }
        if text not in wt_map:
            return {"text": "Please select one of the options."}

        if wt_map[text] == self.WordType.OTHER:
            return self._ask(chat_id, "word_building_missing_word_type_other", "Please enter your own type:")

        sess["word_building"].set_word_type(wt_map[text])
        return self._ask(
            chat_id,
            "word_building_missing_type",
            "What is missing?",
            ["Letters", "Vowels", "Consonants"],
        )

    def word_building_missing_word_type_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty type."}
        sess["word_building"].set_word_type(self.WordType.OTHER, custom)
        return self._ask(
            chat_id,
            "word_building_missing_type",
            "What is missing?",
            ["Letters", "Vowels", "Consonants"],
        )

    def word_building_missing_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        mt_map = {
            "Letters": self.MissingType.LETTERS,
            "Vowels": self.MissingType.VOWELS,
            "Consonants": self.MissingType.CONSONANTS,
        }
        if text not in mt_map:
            return {"text": "Please select one of the options."}

        sess["word_building"].set_missing_type(mt_map[text])
        instruction = sess["word_building"].generate_instruction()
        return self._finish(chat_id, instruction)

    # --- Words from letters ---
    def word_building_words_from_letters_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        wt_map = {
            "Words": self.WordType.WORDS,
            "Nouns": self.WordType.NOUNS,
            "Verbs": self.WordType.VERBS,
            "Adjectives": self.WordType.ADJECTIVES,
            "Other": self.WordType.OTHER,
        }
        if text not in wt_map:
            return {"text": "Please select one of the options."}

        if wt_map[text] == self.WordType.OTHER:
            return self._ask(chat_id, "word_building_words_from_letters_type_other", "Please enter your own type:")

        sess["word_building"].set_word_type(wt_map[text])
        instruction = sess["word_building"].generate_instruction()
        return self._finish(chat_id, instruction)

    def word_building_words_from_letters_type_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty type."}
        sess["word_building"].set_word_type(self.WordType.OTHER, custom)
        instruction = sess["word_building"].generate_instruction()
        return self._finish(chat_id, instruction)

    # --- Forms of words ---
    def word_building_forms_build_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        wt_map = {
            "Words": self.WordType.WORDS,
            "Nouns": self.WordType.NOUNS,
            "Verbs": self.WordType.VERBS,
            "Adjectives": self.WordType.ADJECTIVES,
            "Other": self.WordType.OTHER,
        }
        if text not in wt_map:
            return {"text": "Please select one of the options."}

        if wt_map[text] == self.WordType.OTHER:
            return self._ask(chat_id, "word_building_forms_build_type_other", "Please enter your own type:")

        sess["word_building"].set_build_type(wt_map[text])
        return self._ask(
            chat_id,
            "word_building_forms_given_type",
            "What type of words is given?",
            ["Words", "Nouns", "Verbs", "Adjectives", "Other"],
        )

    def word_building_forms_build_type_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty type."}
        sess["word_building"].set_build_type(self.WordType.OTHER, custom)
        return self._ask(
            chat_id,
            "word_building_forms_given_type",
            "What type of words is given?",
            ["Words", "Nouns", "Verbs", "Adjectives", "Other"],
        )

    def word_building_forms_given_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        wt_map = {
            "Words": self.WordType.WORDS,
            "Nouns": self.WordType.NOUNS,
            "Verbs": self.WordType.VERBS,
            "Adjectives": self.WordType.ADJECTIVES,
            "Other": self.WordType.OTHER,
        }
        if text not in wt_map:
            return {"text": "Please select one of the options."}

        if wt_map[text] == self.WordType.OTHER:
            return self._ask(chat_id, "word_building_forms_given_type_other", "Please enter your own type:")

        sess["word_building"].set_given_type(wt_map[text])
        instruction = sess["word_building"].generate_instruction()
        return self._finish(chat_id, instruction)

    def word_building_forms_given_type_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty type."}
        sess["word_building"].set_given_type(self.WordType.OTHER, custom)
        instruction = sess["word_building"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    #        MATCHING
    # =======================
    def start_matching(self, chat_id: int):
        sess = self._s(chat_id)
        sess["matching"] = self.VocabularyMatching()
        return self._ask(
            chat_id,
            "matching_type",
            "What type of matching task do you want to create?",
            [
                "Sentences to pictures",
                "Descriptions to words",
                "Questions to answers",
                "Other",
                "Back to vocabulary",
            ],
        )

    def matching_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)

        if text == "Back to vocabulary":
            sess["state"] = None
            sess["matching"] = None
            return {"action": "back_to_vocabulary"}

        type_map = {
            "Sentences to pictures": self.MatchingType.SENTENCES_TO_PICTURES,
            "Descriptions to words": self.MatchingType.DESCRIPTIONS_TO_WORDS,
            "Questions to answers": self.MatchingType.QUESTIONS_TO_ANSWERS,
            "Other": self.MatchingType.OTHER,
        }
        if text not in type_map:
            return {"text": "Please select one of the options."}

        sess["matching"].set_matching_type(type_map[text])

        if type_map[text] == self.MatchingType.SENTENCES_TO_PICTURES:
            return self._ask(chat_id, "matching_sentences_range", "How many sentences? Example: 1-6")
        if type_map[text] == self.MatchingType.DESCRIPTIONS_TO_WORDS:
            return self._ask(
                chat_id,
                "matching_desc_word_type",
                "Descriptions for which kind of words?",
                ["Words", "Nouns", "Adjectives", "Verbs", "Other"],
            )
        if type_map[text] == self.MatchingType.QUESTIONS_TO_ANSWERS:
            return self._ask(chat_id, "matching_questions_range", "How many questions? Example: 1-6")
        # OTHER
        return self._ask(chat_id, "matching_other_first", "Match what?")

    # --- Sentences to pictures ---
    def matching_sentences_range(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sess["matching"].set_sentences_range((text or "").strip())
        return self._ask(chat_id, "matching_pictures_range", "How many pictures? Example: a-f")

    def matching_pictures_range(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sess["matching"].set_pictures_range((text or "").strip())
        instruction = sess["matching"].generate_instruction()
        return self._finish(chat_id, instruction)

    # --- Descriptions to words ---
    def matching_desc_word_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        wt_map = {
            "Words": self.MatchingWordType.WORDS,
            "Nouns": self.MatchingWordType.NOUNS,
            "Adjectives": self.MatchingWordType.ADJECTIVES,
            "Verbs": self.MatchingWordType.VERBS,
            "Other": self.MatchingWordType.OTHER,
        }
        if text not in wt_map:
            return {"text": "Please select one of the options."}

        if wt_map[text] == self.MatchingWordType.OTHER:
            return self._ask(chat_id, "matching_desc_word_type_other", "Please enter your own type:")

        sess["matching"].set_desc_word_type(wt_map[text])
        instruction = sess["matching"].generate_instruction()
        return self._finish(chat_id, instruction)

    def matching_desc_word_type_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty type."}
        sess["matching"].set_desc_word_type(self.MatchingWordType.OTHER, custom)
        instruction = sess["matching"].generate_instruction()
        return self._finish(chat_id, instruction)

    # --- Questions to answers ---
    def matching_questions_range(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sess["matching"].set_questions_range((text or "").strip())
        return self._ask(chat_id, "matching_answers_range", "How many answers? Example: a-f")

    def matching_answers_range(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sess["matching"].set_answers_range((text or "").strip())
        instruction = sess["matching"].generate_instruction()
        return self._finish(chat_id, instruction)

    # --- Matching: Other ---
    def matching_other_first(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        first = (text or "").strip()
        if not first:
            return {"text": "Please enter a non-empty value."}
        sess["matching"].set_other_first(first)
        return self._ask(
            chat_id,
            "matching_other_second",
            "Match to what?",
            ["Words", "Nouns", "Adjectives", "Verbs", "Other"],
        )

    def matching_other_second(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        wt_map = {
            "Words": self.MatchingWordType.WORDS,
            "Nouns": self.MatchingWordType.NOUNS,
            "Adjectives": self.MatchingWordType.ADJECTIVES,
            "Verbs": self.MatchingWordType.VERBS,
            "Other": self.MatchingWordType.OTHER,
        }
        if text not in wt_map:
            return {"text": "Please select one of the options."}

        if wt_map[text] == self.MatchingWordType.OTHER:
            return self._ask(chat_id, "matching_other_second_other", "Please enter your own type:")

        sess["matching"].set_other_second(wt_map[text])
        instruction = sess["matching"].generate_instruction()
        return self._finish(chat_id, instruction)

    def matching_other_second_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty type."}
        sess["matching"].set_other_second(self.MatchingWordType.OTHER, custom)
        instruction = sess["matching"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    #     ODD ONE OUT
    # =======================
    def start_odd_one_out(self, chat_id: int):
        sess = self._s(chat_id)
        sess["odd_one_out"] = self.VocabularyOddOneOut()
        return self._ask(
            chat_id,
            "odd_one_out_type",
            "What type of odd one out task do you want to create?",
            [
                "Circle the different word",
                "Circle the word with certain sound",
                "Back to vocabulary",
            ],
        )

    def odd_one_out_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)

        if text == "Back to vocabulary":
            sess["state"] = None
            sess["odd_one_out"] = None
            return {"action": "back_to_vocabulary"}

        type_map = {
            "Circle the different word": self.OddOneOutType.CIRCLE_DIFFERENT,
            "Circle the word with certain sound": self.OddOneOutType.CIRCLE_SOUND,
        }
        if text not in type_map:
            return {"text": "Please select one of the options."}

        sess["odd_one_out"].set_task_type(type_map[text])

        if type_map[text] == self.OddOneOutType.CIRCLE_DIFFERENT:
            return self._ask(
                chat_id,
                "odd_one_out_criterion",
                "What is different?",
                ["Sound", "Meaning", "Other"],
            )

        # CIRCLE_SOUND
        return self._ask(chat_id, "odd_one_out_sound", "Type the sound. Example: /iz/.")

    def odd_one_out_criterion(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        crit_map = {
            "Sound": self.DifferenceCriterion.SOUND,
            "Meaning": self.DifferenceCriterion.MEANING,
            "Other": self.DifferenceCriterion.OTHER,
        }
        if text not in crit_map:
            return {"text": "Please select one of the options."}

        if crit_map[text] == self.DifferenceCriterion.OTHER:
            return self._ask(chat_id, "odd_one_out_criterion_other", "Please enter your own criterion:")

        sess["odd_one_out"].set_criterion(crit_map[text])
        instruction = sess["odd_one_out"].generate_instruction()
        return self._finish(chat_id, instruction)

    def odd_one_out_criterion_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty criterion."}
        sess["odd_one_out"].set_criterion(self.DifferenceCriterion.OTHER, custom)
        instruction = sess["odd_one_out"].generate_instruction()
        return self._finish(chat_id, instruction)

    def odd_one_out_sound(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sound = (text or "").strip()
        if not sound:
            return {"text": "Please enter a non-empty sound (e.g., /iz/)."}
        sess["odd_one_out"].set_sound(sound)
        instruction = sess["odd_one_out"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    #        SYNONYMS
    # =======================
    def start_synonyms(self, chat_id: int):
        sess = self._s(chat_id)
        sess["synonyms"] = self.VocabularySynonyms()
        return self._ask(
            chat_id,
            "synonyms_task_type",
            "What type of task do you want to create?",
            [
                "Choose part of speech out of two",
                "Opposite/similar adjectives",
                "Back to vocabulary",
            ],
        )

    def synonyms_task_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)

        if text == "Back to vocabulary":
            sess["state"] = None
            sess["synonyms"] = None
            return {"action": "back_to_vocabulary"}

        type_map = {
            "Choose part of speech out of two": self.SynonymsTaskType.CHOOSE_POS,
            "Opposite/similar adjectives": self.SynonymsTaskType.OPP_SIM_ADJ,
        }
        if text not in type_map:
            return {"text": "Please select one of the options."}

        sess["synonyms"].set_task_type(type_map[text])

        if type_map[text] == self.SynonymsTaskType.CHOOSE_POS:
            return self._ask(
                chat_id,
                "synonyms_pos1",
                "Choose the first part of speech:",
                ["Nouns", "Pronouns", "Adjectives", "Verbs", "Adverbs", "Other"],
            )

        # OPP_SIM_ADJ
        return self._ask(
            chat_id,
            "synonyms_adj_type",
            "What kind of adjectives?",
            ["Opposite", "Similar"],
        )

    def synonyms_pos1(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        pos_map = {
            "Nouns": self.PartOfSpeech.NOUNS,
            "Pronouns": self.PartOfSpeech.PRONOUNS,
            "Adjectives": self.PartOfSpeech.ADJECTIVES,
            "Verbs": self.PartOfSpeech.VERBS,
            "Adverbs": self.PartOfSpeech.ADVERBS,
            "Other": self.PartOfSpeech.OTHER,
        }
        if text not in pos_map:
            return {
                "text": "Please select one of the options.",
                "options": list(pos_map.keys()),
            }

        if pos_map[text] == self.PartOfSpeech.OTHER:
            return self._ask(chat_id, "synonyms_pos1_other", "Please enter your own part of speech:")

        sess["synonyms"].set_pos1(pos_map[text])
        return self._ask(
            chat_id,
            "synonyms_pos2",
            "Choose the second part of speech:",
            ["Nouns", "Pronouns", "Adjectives", "Verbs", "Adverbs", "Other"],
        )

    def synonyms_pos1_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty part of speech."}
        sess["synonyms"].set_pos1(self.PartOfSpeech.OTHER, custom)
        return self._ask(
            chat_id,
            "synonyms_pos2",
            "Choose the second part of speech:",
            ["Nouns", "Pronouns", "Adjectives", "Verbs", "Adverbs", "Other"],
        )

    def synonyms_pos2(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        pos_map = {
            "Nouns": self.PartOfSpeech.NOUNS,
            "Pronouns": self.PartOfSpeech.PRONOUNS,
            "Adjectives": self.PartOfSpeech.ADJECTIVES,
            "Verbs": self.PartOfSpeech.VERBS,
            "Adverbs": self.PartOfSpeech.ADVERBS,
            "Other": self.PartOfSpeech.OTHER,
        }
        if text not in pos_map:
            return {
                "text": "Please select one of the options.",
                "options": list(pos_map.keys()),
            }

        if pos_map[text] == self.PartOfSpeech.OTHER:
            return self._ask(chat_id, "synonyms_pos2_other", "Please enter your own part of speech:")

        sess["synonyms"].set_pos2(pos_map[text])
        instruction = sess["synonyms"].generate_instruction()
        return self._finish(chat_id, instruction)

    def synonyms_pos2_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty part of speech."}
        sess["synonyms"].set_pos2(self.PartOfSpeech.OTHER, custom)
        instruction = sess["synonyms"].generate_instruction()
        return self._finish(chat_id, instruction)

    def synonyms_adj_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        adj_map = {"Opposite": self.AdjectiveType.OPPOSITE, "Similar": self.AdjectiveType.SIMILAR}
        if text not in adj_map:
            return {"text": "Please select one of the options.", "options": list(adj_map.keys())}

        sess["synonyms"].set_adj_type(adj_map[text])
        instruction = sess["synonyms"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    #   GRAMMAR MULTIPLE CHOICE
    # =======================
    def start_grammar_mc(self, chat_id: int):
        sess = self._s(chat_id)
        sess["grammar_mc"] = self.GrammarMultipleChoice()
        return self._ask(
            chat_id,
            "grammar_mc_type",
            "Choose the type of task:",
            [
                "Circle the correct one",
                "Other",
            ],
        )

    def grammar_mc_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)

        type_map = {
            "Circle the correct one": self.GrammarMultipleChoiceType.CIRCLE_CORRECT,
            "Other": self.GrammarMultipleChoiceType.OTHER,
        }
        if text not in type_map:
            return {
                "text": "Invalid task type. Please choose from the options.",
                "options": list(type_map.keys()),
            }

        sess["grammar_mc"].set_task_type(type_map[text])
        return self._ask(
            chat_id,
            "grammar_mc_subject",
            "Choose the subject:",
            ["Word", "Verb", "Answer", "Other"],
        )

    def grammar_mc_subject(self, chat_id: int, text: str):
        sess = self._s(chat_id)

        subj_map = {
            "Word": self.GrammarMultipleChoiceSubject.WORD,
            "Verb": self.GrammarMultipleChoiceSubject.VERB,
            "Answer": self.GrammarMultipleChoiceSubject.ANSWER,
            "Other": self.GrammarMultipleChoiceSubject.OTHER,
        }
        if text not in subj_map:
            return {
                "text": "Invalid subject. Please choose from the options.",
                "options": list(subj_map.keys()),
            }

        if subj_map[text] == self.GrammarMultipleChoiceSubject.OTHER:
            return self._ask(chat_id, "grammar_mc_subject_other", "Please specify the subject:")

        sess["grammar_mc"].set_subject(subj_map[text])
        instruction = sess["grammar_mc"].generate_instruction()
        return self._finish(chat_id, instruction)

    def grammar_mc_subject_other(self, chat_id: int, subject_other: str):
        sess = self._s(chat_id)
        subject_other = (subject_other or "").strip()
        if not subject_other:
            return {"text": "Please enter a non-empty value."}
        sess["grammar_mc"].set_subject(self.GrammarMultipleChoiceSubject.OTHER, subject_other)
        instruction = sess["grammar_mc"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    #  GRAMMAR COMPLETION
    # =======================
    def start_grammar_completion(self, chat_id: int):
        sess = self._s(chat_id)
        sess["grammar_completion"] = self.GrammarCompletion()
        return self._ask(
            chat_id,
            "grammar_completion_text_type",
            "What should be completed?",
            ["Text", "Sentences", "Conversation", "Other", "Back to grammar"],
        )

    def grammar_completion_text_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text == "Back to grammar":
            sess["state"] = None
            sess["grammar_completion"] = None
            return {"action": "back_to_grammar"}

        text_map = {
            "Text": self.GrammarCompletionTextType.TEXT,
            "Sentences": self.GrammarCompletionTextType.SENTENCES,
            "Conversation": self.GrammarCompletionTextType.CONVERSATION,
            "Other": self.GrammarCompletionTextType.OTHER,
        }
        if text not in text_map:
            return {"text": "Please select one of the options."}

        if text == "Other":
            return self._ask(chat_id, "grammar_completion_text_type_other", "Please enter your own type:")

        sess["grammar_completion"].set_text_type(text_map[text])
        return self._ask(
            chat_id,
            "grammar_completion_task_type",
            f"What type of completing the {text.lower()} task do you want to create?",
            [
                "Correct form of the verbs",
                "Certain form of the verb",
                "Choose one of two forms of the verb",
                "Phrases",
                "Other",
            ],
        )

    def grammar_completion_text_type_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sess["grammar_completion"].set_text_type(self.GrammarCompletionTextType.OTHER, text)
        return self._ask(
            chat_id,
            "grammar_completion_task_type",
            f"What type of completing the {text.lower()} task do you want to create?",
            [
                "Correct form of the verbs",
                "Certain form of the verb",
                "Choose one of two forms of the verb",
                "Phrases",
                "Other",
            ],
        )

    def grammar_completion_task_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        type_map = {
            "Correct form of the verbs": self.GrammarCompletionTaskType.CORRECT_FORM,
            "Certain form of the verb": self.GrammarCompletionTaskType.CERTAIN_FORM,
            "Choose one of two forms of the verb": self.GrammarCompletionTaskType.CHOOSE_TWO,
            "Phrases": self.GrammarCompletionTaskType.PHRASES,
            "Other": self.GrammarCompletionTaskType.OTHER,
        }
        if text not in type_map:
            return {"text": "Please select one of the options."}

        sess["grammar_completion"].set_task_type(type_map[text])

        if type_map[text] == self.GrammarCompletionTaskType.CORRECT_FORM:
            return self._ask(chat_id, "grammar_completion_verbs_given", "Are verbs given?", ["Yes", "No"])
        if type_map[text] == self.GrammarCompletionTaskType.CERTAIN_FORM:
            return self._ask(chat_id, "grammar_completion_tense", "What tense?", [
                "Present Simple", "Present Continuous", "Past Simple", "Past Continuous",
                "Present Perfect", "Past Perfect", "Future Simple", "Other"
            ])
        if type_map[text] == self.GrammarCompletionTaskType.CHOOSE_TWO:
            return self._ask(chat_id, "grammar_completion_tense1", "First tense?", [
                "Present Simple", "Present Continuous", "Past Simple", "Past Continuous",
                "Present Perfect", "Past Perfect", "Future Simple", "Other"
            ])
        if type_map[text] == self.GrammarCompletionTaskType.PHRASES:
            return self._ask(chat_id, "grammar_completion_phrases_given", "Are phrases given?", ["Yes", "No"])
        # OTHER:
        return self._ask(chat_id, "grammar_completion_other_word", "What should be completed with?")

    def grammar_completion_verbs_given(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text not in ["Yes", "No"]:
            return {"text": "Please select Yes or No."}
        sess["grammar_completion"].set_verbs_given(text == "Yes")
        if text == "Yes":
            return self._ask(chat_id, "grammar_completion_where", "Where?", ["in brackets", "in the box", "in the list"])
        instruction = sess["grammar_completion"].generate_instruction()
        return self._finish(chat_id, instruction)

    def grammar_completion_where(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        where_map = {
            "in brackets": self.GrammarCompletionWhere.IN_BRACKETS,
            "in the box": self.GrammarCompletionWhere.IN_BOX,
            "in the list": self.GrammarCompletionWhere.IN_LIST,
        }
        if text not in where_map:
            return {"text": "Please select one of the options."}
        sess["grammar_completion"].set_where(where_map[text])
        instruction = sess["grammar_completion"].generate_instruction()
        return self._finish(chat_id, instruction)

    def grammar_completion_tense(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        allowed = [
            "Present Simple", "Present Continuous", "Past Simple", "Past Continuous",
            "Present Perfect", "Past Perfect", "Future Simple",
        ]
        if text == "Other":
            return self._ask(chat_id, "grammar_completion_tense_custom", "Please enter the tense:")
        if text not in allowed:
            return {"text": "Please select one of the options.", "options": allowed + ["Other"]}
        sess["grammar_completion"].set_tense(text)
        instruction = sess["grammar_completion"].generate_instruction()
        return self._finish(chat_id, instruction)

    def grammar_completion_tense_custom(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sess["grammar_completion"].set_tense(text)
        instruction = sess["grammar_completion"].generate_instruction()
        return self._finish(chat_id, instruction)

    def grammar_completion_tense1(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        allowed = [
            "Present Simple", "Present Continuous", "Past Simple", "Past Continuous",
            "Present Perfect", "Past Perfect", "Future Simple",
        ]
        if text == "Other":
            return self._ask(chat_id, "grammar_completion_tense1_custom", "Please enter the first tense:")
        if text not in allowed:
            return {"text": "Please select one of the options.", "options": allowed + ["Other"]}
        sess["grammar_completion"].set_tenses(text, None)
        return self._ask(chat_id, "grammar_completion_tense2", "Second tense?", allowed + ["Other"])

    def grammar_completion_tense1_custom(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sess["grammar_completion"].set_tenses(text, None)
        return self._ask(chat_id, "grammar_completion_tense2", "Second tense?", [
            "Present Simple", "Present Continuous", "Past Simple", "Past Continuous",
            "Present Perfect", "Past Perfect", "Future Simple", "Other"
        ])

    def grammar_completion_tense2(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        allowed = [
            "Present Simple", "Present Continuous", "Past Simple", "Past Continuous",
            "Present Perfect", "Past Perfect", "Future Simple",
        ]
        if text == "Other":
            return self._ask(chat_id, "grammar_completion_tense2_custom", "Please enter the second tense:")
        if text not in allowed:
            return {"text": "Please select one of the options.", "options": allowed + ["Other"]}
        sess["grammar_completion"].set_tenses(sess["grammar_completion"].tense1, text)
        instruction = sess["grammar_completion"].generate_instruction()
        return self._finish(chat_id, instruction)

    def grammar_completion_tense2_custom(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sess["grammar_completion"].set_tenses(sess["grammar_completion"].tense1, text)
        instruction = sess["grammar_completion"].generate_instruction()
        return self._finish(chat_id, instruction)

    def grammar_completion_phrases_given(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text not in ["Yes", "No"]:
            return {"text": "Please select Yes or No."}
        sess["grammar_completion"].set_phrases_given(text == "Yes")
        if text == "Yes":
            return self._ask(chat_id, "grammar_completion_where", "Where?", ["in brackets", "in the box", "in the list"])
        instruction = sess["grammar_completion"].generate_instruction()
        return self._finish(chat_id, instruction)

    def grammar_completion_other_word(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        word = (text or "").strip()
        if not word:
            return {"text": "Please enter a non-empty value."}
        sess["grammar_completion"].set_other_word(word)
        return self._ask(chat_id, "grammar_completion_other_given", f"{word} are given?", ["Yes", "No"])

    def grammar_completion_other_given(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text not in ["Yes", "No"]:
            return {"text": "Please select Yes or No."}
        sess["grammar_completion"].set_other_given(text == "Yes")
        if text == "Yes":
            return self._ask(chat_id, "grammar_completion_where", "Where?", ["in brackets", "in the box", "in the list"])
        instruction = sess["grammar_completion"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    #  GRAMMAR TRANSFORMATION
    # =======================
    def start_grammar_transformation(self, chat_id: int):
        sess = self._s(chat_id)
        sess["grammar_transformation"] = self.GrammarTransformation()
        return self._ask(
            chat_id,
            "grammar_transformation_type",
            "What type of transformation do you want to create?",
            ["Opposite adjective", "Change tense", "Back to Grammar"],
        )

    def grammar_transformation_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text == "Back to Grammar":
            sess["state"] = None
            sess["grammar_transformation"] = None
            return {"action": "back_to_grammar"}

        type_map = {
            "Opposite adjective": self.GrammarTransformationType.OPPOSITE_ADJECTIVE,
            "Change tense": self.GrammarTransformationType.CHANGE_TENSE,
        }
        if text not in type_map:
            return {"text": "Please select one of the options."}

        sess["grammar_transformation"].set_transformation_type(type_map[text])

        if type_map[text] == self.GrammarTransformationType.OPPOSITE_ADJECTIVE:
            instruction = sess["grammar_transformation"].generate_instruction()
            return self._finish(chat_id, instruction)

        # Change tense → спрашиваем времена
        return self._ask(
            chat_id,
            "grammar_transformation_tense1",
            "What is the initial tense?",
            ["Present Simple", "Present Continuous", "Past Simple", "Past Continuous", "Present Perfect", "Other"],
        )

    def grammar_transformation_tense1(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text == "Other":
            return self._ask(chat_id, "grammar_transformation_tense1_other", "Please enter the initial tense:")

        allowed = ["Present Simple", "Present Continuous", "Past Simple", "Past Continuous", "Present Perfect"]
        if text not in allowed:
            return {"text": "Please select one of the options.", "options": allowed + ["Other"]}

        sess["grammar_transformation"].set_tense1(text)
        return self._ask(
            chat_id,
            "grammar_transformation_tense2",
            "What is the target tense?",
            ["Present Simple", "Present Continuous", "Past Simple", "Past Continuous", "Present Perfect", "Other"],
        )

    def grammar_transformation_tense1_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sess["grammar_transformation"].set_tense1(text)
        return self._ask(
            chat_id,
            "grammar_transformation_tense2",
            "What is the target tense?",
            ["Present Simple", "Present Continuous", "Past Simple", "Past Continuous", "Present Perfect", "Other"],
        )

    def grammar_transformation_tense2(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text == "Other":
            return self._ask(chat_id, "grammar_transformation_tense2_other", "Please enter the target tense:")

        allowed = ["Present Simple", "Present Continuous", "Past Simple", "Past Continuous", "Present Perfect"]
        if text not in allowed:
            return {"text": "Please select one of the options.", "options": allowed + ["Other"]}

        sess["grammar_transformation"].set_tense2(text)
        instruction = sess["grammar_transformation"].generate_instruction()
        return self._finish(chat_id, instruction)

    def grammar_transformation_tense2_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        sess["grammar_transformation"].set_tense2(text)
        instruction = sess["grammar_transformation"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    # GRAMMAR ERROR CORRECTION (переписано на sessions)
    # =======================
    def start_grammar_error_correction(self, chat_id: int):
        sess = self._s(chat_id)
        sess["grammar_error_correction"] = self.GrammarErrorCorrection()
        return self._ask(
            chat_id,
            "grammar_error_correction_type",
            "What is given? (in plural)",
            ["Phrases", "Questions", "Other", "Back to Grammar"],
        )

    def grammar_error_correction_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text == "Back to Grammar":
            sess["state"] = None
            sess["grammar_error_correction"] = None
            return {"action": "back_to_grammar"}

        mapping = {
            "Phrases": self.GivenType.PHRASES,
            "Questions": self.GivenType.QUESTIONS,
            "Other": self.GivenType.OTHER,
        }
        if text not in mapping:
            return {"text": "Please select one of the options."}

        if mapping[text] == self.GivenType.OTHER:
            return self._ask(chat_id, "grammar_error_correction_type_other", "Please enter your own type (in plural):")

        sess["grammar_error_correction"].set_given_type(mapping[text])
        return self._ask(chat_id, "grammar_error_correction_need_correction",
                         f"Is it necessary to correct {text.lower()}?", ["Yes", "No"])

    def grammar_error_correction_type_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty type (in plural)."}
        sess["grammar_error_correction"].set_given_type(self.GivenType.OTHER, custom)
        return self._ask(chat_id, "grammar_error_correction_need_correction",
                         f"Is it necessary to correct {custom.lower()}?", ["Yes", "No"])

    def grammar_error_correction_need_correction(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text not in ["Yes", "No"]:
            return {"text": "Please select Yes or No."}
        sess["grammar_error_correction"].set_need_correction(text == "Yes")
        return self._ask(chat_id, "grammar_error_correction_prep_info",
                         "Any preparatory information given?", ["Yes", "No"])

    def grammar_error_correction_prep_info(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text not in ["Yes", "No"]:
            return {"text": "Please select Yes or No."}

        if text == "No":
            sess["grammar_error_correction"].set_prep_info(self.PrepInfo.NONE)
            instruction = sess["grammar_error_correction"].generate_instruction()
            return self._finish(chat_id, instruction)

        # Yes → выбираем тип
        return self._ask(chat_id, "grammar_error_correction_prep_info_type",
                         "Type of preparatory information:", ["Text", "Audio", "Picture"])

    def grammar_error_correction_prep_info_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        mapping = {
            "Text": self.PrepInfo.TEXT,
            "Audio": self.PrepInfo.AUDIO,
            "Picture": self.PrepInfo.PICTURE,
        }
        if text not in mapping:
            return {"text": "Please select one of the options."}
        sess["grammar_error_correction"].set_prep_info(mapping[text])

        if mapping[text] == self.PrepInfo.TEXT:
            return self._ask(chat_id, "grammar_error_correction_prep_info_clarify",
                             "Clarify the preparatory information:", ["Text", "Story", "Other"])
        elif mapping[text] == self.PrepInfo.AUDIO:
            return self._ask(chat_id, "grammar_error_correction_prep_info_clarify",
                             "Clarify the preparatory information:", ["Dialogue", "Other"])
        elif mapping[text] == self.PrepInfo.PICTURE:
            return self._ask(chat_id, "grammar_error_correction_prep_info_clarify",
                             "Clarify the preparatory information:", ["Picture", "Photo", "Other"])

    def grammar_error_correction_prep_info_clarify(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        prep_info = sess["grammar_error_correction"].prep_info

        valid_options: list[str] = []
        if prep_info == self.PrepInfo.TEXT:
            valid_options = ["Text", "Story", "Other"]
        elif prep_info == self.PrepInfo.AUDIO:
            valid_options = ["Dialogue", "Other"]
        elif prep_info == self.PrepInfo.PICTURE:
            valid_options = ["Picture", "Photo", "Other"]

        if text == "Other":
            return self._ask(chat_id, "grammar_error_correction_prep_info_clarify_other", "Please enter your own type:")
        if text not in valid_options:
            return {"text": "Please select one of the options."}

        sess["grammar_error_correction"].set_prep_info_clarify(text)
        instruction = sess["grammar_error_correction"].generate_instruction()
        return self._finish(chat_id, instruction)

    def grammar_error_correction_prep_info_clarify_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty value."}
        sess["grammar_error_correction"].set_prep_info_clarify(custom)
        instruction = sess["grammar_error_correction"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    #   READING MULTIPLE CHOICE
    # =======================
    def start_reading_multiple_choice(self, chat_id: int):
        sess = self._s(chat_id)
        sess["reading_mc"] = self.ReadingMultipleChoice()
        return self._ask(
            chat_id,
            "reading_multiple_choice_type",
            "What type of text is given?",
            ["Text", "Story", "Dialogue", "Other", "Back to Reading"],
        )

    def reading_multiple_choice_type(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        if text == "Back to Reading":
            sess["state"] = None
            sess["reading_mc"] = None
            return {"action": "back_to_reading"}

        type_map = {
            "Text": self.ReadingTextType.TEXT,
            "Story": self.ReadingTextType.STORY,
            "Dialogue": self.ReadingTextType.DIALOGUE,
        }

        if text == "Other":
            return self._ask(chat_id, "reading_multiple_choice_type_other", "Please enter your own type:")

        if text not in type_map:
            return {"text": "Please select one of the options."}

        sess["reading_mc"].set_text_type(type_map[text])
        instruction = sess["reading_mc"].generate_instruction()
        return self._finish(chat_id, instruction)

    def reading_multiple_choice_type_other(self, chat_id: int, text: str):
        sess = self._s(chat_id)
        custom = (text or "").strip()
        if not custom:
            return {"text": "Please enter a non-empty type."}
        sess["reading_mc"].set_text_type(self.ReadingTextType.OTHER, custom)
        instruction = sess["reading_mc"].generate_instruction()
        return self._finish(chat_id, instruction)

    # =======================
    #    READING TRUE/FALSE
    # =======================
    def start_reading_true_false(self, chat_id: int):
        sess = self._s(chat_id)
        sess["reading_tf"] = self.ReadingTrueFalse()
        return self._ask(
            chat_id,
            "reading_true_false_read_first",
            "Ask to read the text first?",
            ["Yes", "No", "Back to Reading"],
        )

    def reading_true_false_read_first(self, chat_id: int, text: str):
        sess = self._s(chat_id)

        if text == "Back to Reading":
            sess["state"] = None
            sess["reading_tf"] = None
            return {"action": "back_to_reading"}

        if text not in ["Yes", "No"]:
            return {"text": "Please select Yes or No."}

        sess["reading_tf"].set_read_first(text == "Yes")
        instruction = sess["reading_tf"].generate_instruction()
        return self._finish(chat_id, instruction)