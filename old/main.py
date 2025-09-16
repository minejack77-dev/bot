# main.py
import asyncio
import logging
from logging.handlers import RotatingFileHandle
from os import getenv

from aiogram import Bot, Dispatcher, F, BaseMiddleware
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv
from db_utils import init_db, log_user_action

from generation import CreateTaskFormulation

load_dotenv()
BOT_TOKEN = getenv("BOT_TOKEN")

LOG_FILE = "bot.log"
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8"),
        logging.StreamHandler()
    ],
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger("bot")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

async def main():
    logger.info("Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# --- Middleware for DB logging ---
class DBLoggerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if isinstance(event, Message) and event.from_user:
            uid = event.from_user.id
            uname = event.from_user.username or event.from_user.full_name
            action_text = (event.text or "").strip()
            try:
                log_user_action(uid, uname, action_text)
            except Exception as e:
                logger.exception("DB log failed: %s", e)
        return await handler(event, data)
    
dp.message.middleware(DBLoggerMiddleware())

# единый формулятор
formulator = CreateTaskFormulation()

# --- быстрые клавиатуры ---
def main_menu_kb():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Create task formulation")],
            [KeyboardButton(text="Help")]
        ]
    )

def sections_kb():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Vocabulary")],
            [KeyboardButton(text="Grammar")],
            [KeyboardButton(text="Reading")],
            [KeyboardButton(text="Back to main menu")],
        ]
    )

def vocabulary_menu_kb():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Labelling")],
            [KeyboardButton(text="Categorisation")],
            [KeyboardButton(text="Word-building")],
            [KeyboardButton(text="Matching")],
            [KeyboardButton(text="Odd one out")],
            [KeyboardButton(text="Synonyms/antonyms/definitions/lexical sets")],
            [KeyboardButton(text="Back to sections")],
        ]
    )

def grammar_menu_kb():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Grammar Multiple Choice")],
            [KeyboardButton(text="Sentence/dialogue completion")],
            [KeyboardButton(text="Transformation")],
            [KeyboardButton(text="Error Correction")],
            [KeyboardButton(text="Back to sections")],
        ]
    )

def reading_menu_kb():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Reading Multiple Choice")],
            [KeyboardButton(text="True/False")],
            [KeyboardButton(text="Back to sections")],
        ]
    )

BOT_DESCRIPTION = (
    "Welcome! This bot helps generate clear English task formulations.\n\n"
    "Tap 'Create task formulation' to start, pick a section, then answer a few prompts. "
    "You'll get a ready-to-use instruction."
)

# ---------- утилита отправки ответа ----------
async def send_result(message: Message, result: dict, after_done_kb: ReplyKeyboardMarkup | None = None):
    """
    Универсальная отправка ответов от generation.py:
    - если есть options → показываем клавиатуру с ними
    - если action == done → показываем кнопки возврата в разделы
    """
    if not result:
        return

    # если закончили — показать кнопки возврата для текущего раздела
    if result.get("action") == "done":
        section = formulator._s(message.chat.id).get("task_type")
        if section == "grammar":
            kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
                [KeyboardButton(text="Back to Grammar")],
                [KeyboardButton(text="Back to sections")],
                [KeyboardButton(text="Back to main menu")],
            ])
        elif section == "reading":
            kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
                [KeyboardButton(text="Back to Reading")],
                [KeyboardButton(text="Back to sections")],
                [KeyboardButton(text="Back to main menu")],
            ])
        else:
            kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
                [KeyboardButton(text="Back to Vocabulary")],
                [KeyboardButton(text="Back to sections")],
                [KeyboardButton(text="Back to main menu")],
            ])
        await message.answer(result["text"], reply_markup=kb)
        return

    # если нам прислали варианты — показать их
    if "options" in result:
        kb = ReplyKeyboardMarkup(resize_keyboard=True,
                                 keyboard=[[KeyboardButton(text=o)] for o in result["options"]])
        await message.answer(result["text"], reply_markup=kb)
    else:
        await message.answer(result["text"], reply_markup=after_done_kb)

# ---------- команды ----------
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(BOT_DESCRIPTION, reply_markup=main_menu_kb())

@dp.message(Command("menu"))
async def cmd_menu(message: Message):
    # полный сброс
    formulator.reset_session(message.chat.id, None)
    await message.answer("Main menu. Please select an option:", reply_markup=main_menu_kb())

# ---------- навигация верхнего уровня ----------
@dp.message(F.text == "Help")
async def handle_help(message: Message):
    await message.answer(BOT_DESCRIPTION, reply_markup=main_menu_kb())

@dp.message(F.text == "Back to main menu")
async def handle_back_to_main(message: Message):
    formulator.reset_session(message.chat.id, None)
    await message.answer("Main menu. Please select an option:", reply_markup=main_menu_kb())

@dp.message(F.text == "Back to sections")
async def handle_back_to_sections(message: Message):
    await message.answer("Select a section:", reply_markup=sections_kb())

@dp.message(F.text == "Create task formulation")
async def handle_create_task_formulation(message: Message):
    await message.answer("Select a section:", reply_markup=sections_kb())

# ---------- разделы ----------
@dp.message(F.text == "Vocabulary")
async def handle_vocabulary(message: Message):
    formulator.set_task_type(message.chat.id, "vocabulary")
    await message.answer("Vocabulary tasks:", reply_markup=vocabulary_menu_kb())

@dp.message(F.text == "Grammar")
async def handle_grammar(message: Message):
    formulator.set_task_type(message.chat.id, "grammar")
    await message.answer("Grammar tasks:", reply_markup=grammar_menu_kb())

@dp.message(F.text == "Reading")
async def handle_reading(message: Message):
    formulator.set_task_type(message.chat.id, "reading")
    await message.answer("Reading tasks:", reply_markup=reading_menu_kb())

# ---------- Vocabulary: старты ----------
@dp.message(F.text == "Labelling")
async def start_labelling(message: Message):
    res = formulator.start_labelling(message.chat.id)
    await send_result(message, res)

@dp.message(F.text == "Categorisation")
async def start_categorising(message: Message):
    res = formulator.start_categorising(message.chat.id)
    await send_result(message, res)

@dp.message(F.text == "Word-building")
async def start_word_building(message: Message):
    res = formulator.start_word_building(message.chat.id)
    await send_result(message, res)

@dp.message(F.text == "Matching")
async def start_matching(message: Message):
    res = formulator.start_matching(message.chat.id)
    await send_result(message, res)

@dp.message(F.text == "Odd one out")
async def start_odd_one_out(message: Message):
    res = formulator.start_odd_one_out(message.chat.id)
    await send_result(message, res)

@dp.message(F.text == "Synonyms/antonyms/definitions/lexical sets")
async def start_synonyms(message: Message):
    res = formulator.start_synonyms(message.chat.id)
    await send_result(message, res)

# ---------- Grammar: старты ----------
@dp.message(F.text == "Grammar Multiple Choice")
async def start_grammar_mc(message: Message):
    res = formulator.start_grammar_mc(message.chat.id)
    await send_result(message, res)

@dp.message(F.text == "Sentence/dialogue completion")
async def start_grammar_completion(message: Message):
    res = formulator.start_grammar_completion(message.chat.id)
    await send_result(message, res)

@dp.message(F.text == "Transformation")
async def start_grammar_transformation(message: Message):
    res = formulator.start_grammar_transformation(message.chat.id)
    await send_result(message, res)

@dp.message(F.text == "Error Correction")
async def start_grammar_error_correction(message: Message):
    res = formulator.start_grammar_error_correction(message.chat.id)
    await send_result(message, res)

# ---------- Reading: старты ----------
@dp.message(F.text == "Reading Multiple Choice")
async def start_reading_mc(message: Message):
    res = formulator.start_reading_multiple_choice(message.chat.id)
    await send_result(message, res)

@dp.message(F.text == "True/False")
async def start_reading_tf(message: Message):
    res = formulator.start_reading_true_false(message.chat.id)
    await send_result(message, res)

# ---------- кнопки "назад" в разделах ----------
@dp.message(F.text == "Back to Vocabulary")
async def back_to_vocabulary(message: Message):
    await handle_vocabulary(message)

@dp.message(F.text == "Back to Grammar")
async def back_to_grammar(message: Message):
    await handle_grammar(message)

@dp.message(F.text == "Back to Reading")
async def back_to_reading(message: Message):
    await handle_reading(message)

# ---------- ЕДИНЫЙ роутер состояний ----------
# Сопоставление state -> метода в generation.py
STATE_TO_HANDLER = {
    # Labelling
    "labelling_label_type": formulator.labelling_label_type,
    "labelling_label_type_other": formulator.labelling_label_type_other,
    "labelling_task_format": formulator.labelling_task_format,
    "labelling_word_list_option": formulator.labelling_word_list_option,

    # Categorising
    "categorising_task_type": formulator.categorising_task_type,
    "categorising_table_type": formulator.categorising_table_type,
    "categorising_table_type_other": formulator.categorising_table_type_other,

    # Word-building
    "word_building_task_type": formulator.word_building_task_type,
    "word_building_missing_word_type": formulator.word_building_missing_word_type,
    "word_building_missing_word_type_other": formulator.word_building_missing_word_type_other,
    "word_building_missing_type": formulator.word_building_missing_type,
    "word_building_words_from_letters_type": formulator.word_building_words_from_letters_type,
    "word_building_words_from_letters_type_other": formulator.word_building_words_from_letters_type_other,
    "word_building_forms_build_type": formulator.word_building_forms_build_type,
    "word_building_forms_build_type_other": formulator.word_building_forms_build_type_other,
    "word_building_forms_given_type": formulator.word_building_forms_given_type,
    "word_building_forms_given_type_other": formulator.word_building_forms_given_type_other,

    # Matching
    "matching_type": formulator.matching_type,
    "matching_sentences_range": formulator.matching_sentences_range,
    "matching_pictures_range": formulator.matching_pictures_range,
    "matching_desc_word_type": formulator.matching_desc_word_type,
    "matching_desc_word_type_other": formulator.matching_desc_word_type_other,
    "matching_questions_range": formulator.matching_questions_range,
    "matching_answers_range": formulator.matching_answers_range,
    "matching_other_first": formulator.matching_other_first,
    "matching_other_second": formulator.matching_other_second,
    "matching_other_second_other": formulator.matching_other_second_other,

    # Odd one out
    "odd_one_out_type": formulator.odd_one_out_type,
    "odd_one_out_criterion": formulator.odd_one_out_criterion,
    "odd_one_out_criterion_other": formulator.odd_one_out_criterion_other,
    "odd_one_out_sound": formulator.odd_one_out_sound,

    # Synonyms
    "synonyms_task_type": formulator.synonyms_task_type,
    "synonyms_pos1": formulator.synonyms_pos1,
    "synonyms_pos1_other": formulator.synonyms_pos1_other,
    "synonyms_pos2": formulator.synonyms_pos2,
    "synonyms_pos2_other": formulator.synonyms_pos2_other,
    "synonyms_adj_type": formulator.synonyms_adj_type,

    # Grammar MC
    "grammar_mc_type": formulator.grammar_mc_type,
    "grammar_mc_subject": formulator.grammar_mc_subject,
    "grammar_mc_subject_other": formulator.grammar_mc_subject_other,

    # Grammar completion
    "grammar_completion_text_type": formulator.grammar_completion_text_type,
    "grammar_completion_text_type_other": formulator.grammar_completion_text_type_other,
    "grammar_completion_task_type": formulator.grammar_completion_task_type,
    "grammar_completion_verbs_given": formulator.grammar_completion_verbs_given,
    "grammar_completion_where": formulator.grammar_completion_where,
    "grammar_completion_tense": formulator.grammar_completion_tense,
    "grammar_completion_tense_custom": formulator.grammar_completion_tense_custom,
    "grammar_completion_tense1": formulator.grammar_completion_tense1,
    "grammar_completion_tense1_custom": formulator.grammar_completion_tense1_custom,
    "grammar_completion_tense2": formulator.grammar_completion_tense2,
    "grammar_completion_tense2_custom": formulator.grammar_completion_tense2_custom,
    "grammar_completion_phrases_given": formulator.grammar_completion_phrases_given,
    "grammar_completion_other_word": formulator.grammar_completion_other_word,
    "grammar_completion_other_given": formulator.grammar_completion_other_given,

    # Grammar transformation
    "grammar_transformation_type": formulator.grammar_transformation_type,
    "grammar_transformation_tense1": formulator.grammar_transformation_tense1,
    "grammar_transformation_tense1_other": formulator.grammar_transformation_tense1_other,
    "grammar_transformation_tense2": formulator.grammar_transformation_tense2,
    "grammar_transformation_tense2_other": formulator.grammar_transformation_tense2_other,

    # Grammar error correction
    "grammar_error_correction_type": formulator.grammar_error_correction_type,
    "grammar_error_correction_type_other": formulator.grammar_error_correction_type_other,
    "grammar_error_correction_need_correction": formulator.grammar_error_correction_need_correction,
    "grammar_error_correction_prep_info": formulator.grammar_error_correction_prep_info,
    "grammar_error_correction_prep_info_type": formulator.grammar_error_correction_prep_info_type,
    "grammar_error_correction_prep_info_clarify": formulator.grammar_error_correction_prep_info_clarify,
    "grammar_error_correction_prep_info_clarify_other": formulator.grammar_error_correction_prep_info_clarify_other,

    # Reading MC + TF
    "reading_multiple_choice_type": formulator.reading_multiple_choice_type,
    "reading_multiple_choice_type_other": formulator.reading_multiple_choice_type_other,
    "reading_true_false_read_first": formulator.reading_true_false_read_first,
}

@dp.message()  # универсальный обработчик "шага мастера"
async def handle_step(message: Message):
    state = formulator.get_state(message.chat.id)
    if not state:
        # нет активного шага — подскажем пользователю вернуться в меню
        return await message.answer(
            "Choose an option from the menu 🙂",
            reply_markup=main_menu_kb()
        )
    handler = STATE_TO_HANDLER.get(state)
    if not handler:
        return await message.answer("Something went wrong. Try /menu")
    result = handler(message.chat.id, message.text)
    await send_result(message, result)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())