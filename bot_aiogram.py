import asyncio
import logging
from typing import Any, Dict, Optional

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import CommandStart, Command, Text
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from config import BOT_TOKEN
# ВАЖНО: тут твой класс из generation.py
# Должен иметь методы start_* и последующие шаги, как в твоём коде,
# и хранить состояние в _s(chat_id)["state"] (или иметь get_state()).
from generation import CreateTaskFormulation


# -------------------- базовая настройка --------------------
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
rt = Router()
dp.include_router(rt)

gen = CreateTaskFormulation()  # единый формировщик из generation.py


# -------------------- текст помощи --------------------
BOT_DESCRIPTION = (
    "Welcome to the Task Formulation Bot!\n\n"
    "This bot helps English teachers and learners generate clear, ready-to-use instructions for many task types.\n\n"
    "How to use:\n"
    "• Press 'Create task formulation'\n"
    "• Pick a section (Vocabulary / Grammar / Reading)\n"
    "• Answer a few short questions using buttons\n"
    "• Receive a finished instruction you can paste into your worksheet\n"
)


# -------------------- клавиатуры --------------------
def kb(options: list[str]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=o)] for o in options],
        resize_keyboard=True
    )

def kb_main() -> ReplyKeyboardMarkup:
    return kb(["Create task formulation", "Help"])

def kb_sections() -> ReplyKeyboardMarkup:
    return kb(["Vocabulary", "Grammar", "Reading", "Back to main menu"])

def kb_vocab() -> ReplyKeyboardMarkup:
    return kb([
        "Labelling",
        "Categorisation",
        "Word-building",
        "Matching",
        "Odd one out",
        "Synonyms/antonyms/definitions/lexical sets",
        "Back to sections",
    ])

def kb_grammar() -> ReplyKeyboardMarkup:
    return kb([
        "Grammar Multiple Choice",
        "Sentence/dialogue completion",
        "Transformation",
        "Error Correction",
        "Back to sections",
    ])

def kb_reading() -> ReplyKeyboardMarkup:
    return kb([
        "Reading Multiple Choice",
        "True/False",
        "Back to sections",
    ])

def kb_after_done(section: str) -> ReplyKeyboardMarkup:
    # section ∈ {'vocabulary','grammar','reading'}
    back_map = {
        "grammar": "Back to Grammar",
        "reading": "Back to Reading",
        "vocabulary": "Back to Vocabulary",
    }
    return kb([back_map.get(section, "Back to Vocabulary"), "Back to sections", "Back to main menu"])


# -------------------- вспомогательные адаптеры --------------------
def get_state(formulator: Any, chat_id: int) -> Optional[str]:
    """Пытаемся получить текущее состояние из класса generation."""
    if hasattr(formulator, "get_state"):
        try:
            return formulator.get_state(chat_id)
        except Exception:
            pass
    try:
        return formulator._s(chat_id).get("state")
    except Exception:
        return None

def set_task_type(formulator: Any, chat_id: int, section: str) -> None:
    """Сохраняем текущий раздел в сессии — чтобы знать, какие back-кнопки показать после 'done'."""
    try:
        sess = formulator._s(chat_id)
        sess["task_type"] = section.lower()
    except Exception:
        pass

def get_task_type(formulator: Any, chat_id: int) -> str:
    try:
        return (formulator._s(chat_id).get("task_type") or "vocabulary").lower()
    except Exception:
        return "vocabulary"


async def render_step(message: Message, result: Dict[str, Any]):
    """Единая отрисовка ответа шага."""
    if not result:
        await message.answer("Something went wrong. Please try again.")
        return

    # финальный шаг
    if result.get("action") == "done":
        section = get_task_type(gen, message.chat.id)
        text = result.get("text") or ""
        # Добавляем требуемый префикс
        if not text.startswith("Here's your task formulation:"):
            text = "Here's your task formulation:\n" + text.replace("Task formulation:\n", "").replace("Task formulation:", "").strip()
        await message.answer(text, reply_markup=kb_after_done(section))
        return

    # промежуточные шаги
    if "options" in result:
        await message.answer(result.get("text") or "Choose:", reply_markup=kb(list(map(str, result["options"]))))
    else:
        await message.answer(result.get("text") or "OK")


# -------------------- стартовые команды --------------------
@rt.message(CommandStart())
async def on_start(message: Message):
    await message.answer(BOT_DESCRIPTION, reply_markup=kb_main())

@rt.message(Command("menu"))
async def on_menu(message: Message):
    await message.answer("Main menu. Please select an option:", reply_markup=kb_main())

@rt.message(Text("Help"))
async def on_help(message: Message):
    await message.answer(BOT_DESCRIPTION, reply_markup=kb_main())

@rt.message(Text("Back to main menu"))
async def on_back_main(message: Message):
    await message.answer("Main menu. Please select an option:", reply_markup=kb_main())


# -------------------- основной пункт: Create --------------------
@rt.message(Text("Create task formulation"))
async def on_create(message: Message):
    await message.answer("Select a section:", reply_markup=kb_sections())


# -------------------- разделы и входные точки сценариев --------------------
@rt.message(Text("Back to sections"))
async def back_to_sections(message: Message):
    await message.answer("Select a section:", reply_markup=kb_sections())

@rt.message(Text("Vocabulary"))
async def on_vocab(message: Message):
    await message.answer("Vocabulary tasks:", reply_markup=kb_vocab())

@rt.message(Text("Grammar"))
async def on_grammar(message: Message):
    await message.answer("Grammar tasks:", reply_markup=kb_grammar())

@rt.message(Text("Reading"))
async def on_reading(message: Message):
    await message.answer("Reading tasks:", reply_markup=kb_reading())


# ВХОДНЫЕ КНОПКИ ДЛЯ КАЖДОГО СЦЕНАРИЯ

@rt.message(Text("Labelling"))
async def start_labelling(message: Message):
    set_task_type(gen, message.chat.id, "vocabulary")
    res = gen.start_labelling(message.chat.id)
    await render_step(message, res)

@rt.message(Text("Categorisation"))
async def start_categorisation(message: Message):
    set_task_type(gen, message.chat.id, "vocabulary")
    res = gen.start_categorising(message.chat.id)
    await render_step(message, res)

@rt.message(Text("Word-building"))
async def start_word_building(message: Message):
    set_task_type(gen, message.chat.id, "vocabulary")
    res = gen.start_word_building(message.chat.id)
    await render_step(message, res)

@rt.message(Text("Matching"))
async def start_matching(message: Message):
    set_task_type(gen, message.chat.id, "vocabulary")
    res = gen.start_matching(message.chat.id)
    await render_step(message, res)

@rt.message(Text("Odd one out"))
async def start_odd_one_out(message: Message):
    set_task_type(gen, message.chat.id, "vocabulary")
    res = gen.start_odd_one_out(message.chat.id)
    await render_step(message, res)

@rt.message(Text("Synonyms/antonyms/definitions/lexical sets"))
async def start_synonyms(message: Message):
    set_task_type(gen, message.chat.id, "vocabulary")
    res = gen.start_synonyms(message.chat.id)
    await render_step(message, res)

@rt.message(Text("Grammar Multiple Choice"))
async def start_grammar_mc(message: Message):
    set_task_type(gen, message.chat.id, "grammar")
    res = gen.start_grammar_mc(message.chat.id)
    await render_step(message, res)

@rt.message(Text("Sentence/dialogue completion"))
async def start_grammar_completion(message: Message):
    set_task_type(gen, message.chat.id, "grammar")
    res = gen.start_grammar_completion(message.chat.id)
    await render_step(message, res)

@rt.message(Text("Transformation"))
async def start_grammar_transformation(message: Message):
    set_task_type(gen, message.chat.id, "grammar")
    res = gen.start_grammar_transformation(message.chat.id)
    await render_step(message, res)

@rt.message(Text("Error Correction"))
async def start_grammar_error_correction(message: Message):
    set_task_type(gen, message.chat.id, "grammar")
    res = gen.start_grammar_error_correction(message.chat.id)
    await render_step(message, res)

@rt.message(Text("Reading Multiple Choice"))
async def start_reading_mc(message: Message):
    set_task_type(gen, message.chat.id, "reading")
    res = gen.start_reading_multiple_choice(message.chat.id)
    await render_step(message, res)

@rt.message(Text("True/False"))
async def start_reading_tf(message: Message):
    set_task_type(gen, message.chat.id, "reading")
    res = gen.start_reading_true_false(message.chat.id)
    await render_step(message, res)


# -------------------- УНИВЕРСАЛЬНЫЙ ОБРАБОТЧИК ШАГОВ --------------------
@rt.message(F.text)
async def state_driver(message: Message):
    """
    Универсальный обработчик: берёт текущее состояние из generation
    и вызывает метод с таким же именем, передавая (chat_id, text).
    """
    st = get_state(gen, message.chat.id)
    if not st:
        return  # вне сценария
    if not hasattr(gen, st):
        # неизвестное состояние — просто ничего не делаем
        return
    func = getattr(gen, st)
    res = func(message.chat.id, message.text or "")
    await render_step(message, res)


# -------------------- запуск --------------------
async def main():
    await dp.start_polling(bot, allowed_updates=["message"])

if __name__ == "__main__":
    asyncio.run(main())