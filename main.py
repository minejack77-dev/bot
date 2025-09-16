# main.py
import asyncio
import logging
from os import getenv
from logging.handlers import RotatingFileHandler  # ← добавлено

from aiogram import Bot, Dispatcher, F, BaseMiddleware  # ← добавлено BaseMiddleware
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters import CommandStart, Command
from dotenv import load_dotenv

from generation import CreateTaskFormulation
from db_utils import init_db, log_user_action  # ← добавлено

load_dotenv()
BOT_TOKEN = getenv("BOT_TOKEN")
FEEDBACK_WAITING: set[int] = set()

# --- базовая настройка логов (оставлено как у тебя) ---
logging.basicConfig(level=logging.INFO)

# --- + файл-лог с ротацией (добавлено) ---hjjlkhnjklhjklhjklh
LOG_FILE = "bot.log"
_file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
logging.getLogger().addHandler(_file_handler)
logger = logging.getLogger("bot")

# --- инициализация БД (добавлено) ---
init_db()

# --- проверка токена (добавлено, но необязательно) ---
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Add it to .env (BOT_TOKEN=1234:ABC...)")

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# --- Middleware для логирования действий в БД (добавлено) ---
class DBLoggerMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        # логируем только входящие сообщения от пользователей
        if isinstance(event, Message) and event.from_user:
            uid = event.from_user.id
            uname = event.from_user.username or event.from_user.full_name
            action_text = (event.text or "").strip()
            try:
                log_user_action(uid, uname, action_text)
            except Exception as e:
                logger.exception("DB log failed: %s", e)
        return await handler(event, data)

# регистрация мидлвари (добавлено)
dp.message.middleware(DBLoggerMiddleware())

# единый формулятор
formulator = CreateTaskFormulation()

# --- быстрые клавиатуры ---

async def answer_with_keyboard(message, result: dict):
    """
    Универсальный ответчик:
    - если есть options -> рисуем клавиатуру с кнопками
    - если action == 'done' -> показываем финал и кнопки навигации
    - иначе просто отправляем текст
    """
    if not result:
        return

    # Финальный шаг
    if result.get("action") == "done":
        kb = ReplyKeyboardMarkup(
            resize_keyboard=True,
            keyboard=[
                [KeyboardButton(text="Back to sections")],
                [KeyboardButton(text="Back to main menu")],
            ],
        )
        await message.answer(result["text"], reply_markup=kb)
        return

    # Вопрос с вариантами
    if "options" in result and isinstance(result["options"], (list, tuple)):
        rows = [[KeyboardButton(text=opt)] for opt in result["options"]]
        kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=rows)
        await message.answer(result["text"], reply_markup=kb)
        return

    # Простой текст
    await message.answer(result.get("text", ""))

def main_menu_kb():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="Create task formulation")],
            [KeyboardButton(text="Practice task formulation")],
            [KeyboardButton(text="Feedback")],
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
    "Welcome to the Task Formulation Bot!\n\n"
    "This bot helps English teachers and learners to quickly generate, practice, and manage various types of language tasks for lessons and self-study.\n\n"
    "Main Features:\n"
    "1. Create Task Formulation\n"
    "   - Instantly generate clear and professional instructions for a wide variety of English tasks.\n"
    "   - Supported task types include:\n"
    "     • Vocabulary (labelling, categorisation, word-building, matching, odd one out, synonyms/antonyms/definitions/lexical sets)\n"
    "     • Grammar (multiple choice, sentence/dialogue completion, transformation, error correction)\n"
    "     • Reading (multiple choice questions)\n"
    "   - The bot will guide you step by step, asking for all necessary parameters and helping you choose the right task format.\n\n"
    "2. Practice Task Formulation (CURRENTLY UNAVAILABLE!!!)\n"
    "   - Practice formulating instructions for different types of tasks.\n"
    "   - The bot will show you a task body (e.g., a picture or text) and you will try to write the correct instruction.\n"
    "   - After your attempt, you can check the correct answer and compare it with your own.\n\n"
    "3. Feedback\n"
    "   - You can send any feedback, suggestions, or questions to the developer at any time using the 'Feedback' button in the main menu.\n\n"
    "4. Help\n"
    "   - At any time, press the 'Help' button to see this description and get guidance on how to use the bot.\n\n"
    "How to use:\n"
    "- Use the main menu to select what you want to do: create a task, practice, get help, or send feedback.\n"
    "- Follow the on-screen instructions and choose options using the provided buttons.\n"
    "- For each task type, the bot will ask you a series of questions to clarify the details and then generate a ready-to-use instruction.\n"
    "- In practice mode, try to formulate the instruction yourself and check your answer.\n\n"
    "Who is this bot for?\n"
    "- English teachers who want to save time and get high-quality task instructions.\n"
    "- Students who want to practice understanding and formulating task instructions.\n"
    "- Anyone interested in English language learning and teaching.\n\n"
    "Your actions in the bot are logged for quality improvement and support. All feedback is welcome!\n\n"
    "If you have any questions, just press 'Help' or 'Feedback'. Enjoy using the bot!"
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


@dp.message(F.text == "Feedback")
async def h_feedback(message: Message):
    FEEDBACK_WAITING.add(message.chat.id)
    await message.answer(
        "We’d love to hear your thoughts!\n\n"
        "Please type your feedback below. Send /cancel to stop."
    )

@dp.message(Command("cancel"))
async def h_cancel(message: Message):
    if message.chat.id in FEEDBACK_WAITING:
        FEEDBACK_WAITING.discard(message.chat.id)
        await message.answer("Feedback cancelled. Back to main menu.")

@dp.message(lambda m: m.chat.id in FEEDBACK_WAITING)
async def h_feedback_text(message: Message):
    text = (message.text or "").strip()
    if not text:
        await message.answer("Please send text feedback or /cancel.")
        return

    # логируем как обычное действие
    log_user_action(
        user_id=message.from_user.id,
        username=message.from_user.username or message.from_user.full_name,
        action=f"FEEDBACK: {text}",
    )

    FEEDBACK_WAITING.discard(message.chat.id)
    await message.answer("Thank you! Your feedback has been recorded 🙌")

@dp.message(F.text == "Practice task formulation")
async def h_practice(message: Message):
    await message.answer("Currently unavailable.")

# --- EXTRA QUESTIONS (должны идти ДО fallback'ов) ---

# 1) Do you want to give additional instructions? -> Yes/No
@dp.message(F.text.in_({"+", "-"}))
async def h_additional_instructions(message: Message):
    if formulator.get_state(message.chat.id) != "additional_instructions":
        return  # не наш шаг — пропускаем
    result = formulator.additional_instructions(message.chat.id, message.text)
    await answer_with_keyboard(message, result)

# 2) How do you prefer students to work? -> Individually / In pairs / In groups
@dp.message(F.text.in_({"Individually", "In pairs", "In groups"}))
async def h_extras_work_mode(message: Message):
    if formulator.get_state(message.chat.id) != "extras_work_mode":
        return
    result = formulator.extras_work_mode(message.chat.id, message.text)
    await answer_with_keyboard(message, result)

# 3) How much time do your students have? -> 1 min / 2 mins / 3 mins
@dp.message(F.text.in_({"1 min", "2 mins", "3 mins"}))
async def h_extras_time(message: Message):
    if formulator.get_state(message.chat.id) != "extras_time":
        return
    result = formulator.extras_time(message.chat.id, message.text)
    await answer_with_keyboard(message, result)

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


# === helpers ===
def _make_kb(options: list[str] | None):
    if not options:
        return None
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=o)] for o in options],
        resize_keyboard=True
    )

async def answer_with_keyboard(message: Message, result: dict):
    """
    Универсальная отправка ответа:
    - если в result есть 'options' — рисуем клавиатуру с кнопками
    - если action == 'done' — показываем «Back to sections / Back to main menu»
    """
    if not result:
        return

    # Если сценарий завершён
    if result.get("action") == "done":
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Back to sections")],
                [KeyboardButton(text="Back to main menu")],
            ],
            resize_keyboard=True
        )
        await message.answer(result["text"], reply_markup=kb)
        return

    # Иначе просто шаг с вариантами
    kb = _make_kb(result.get("options"))
    await message.answer(result["text"], reply_markup=kb)

# === helpers for extra-step replies ===
def _make_kb(options: list[str] | None):
    if not options:
        return None
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=o)] for o in options],
        resize_keyboard=True
    )

async def answer_with_keyboard(message: Message, result: dict):
    """Универсальная отправка ответа с клавиатурой."""
    if not result:
        return
    # финал сценария
    if result.get("action") == "done":
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Back to sections")],
                [KeyboardButton(text="Back to main menu")],
            ],
            resize_keyboard=True,
        )
        await message.answer(result["text"], reply_markup=kb)
        return
    # промежуточный шаг
    kb = _make_kb(result.get("options"))
    await message.answer(result["text"], reply_markup=kb)
