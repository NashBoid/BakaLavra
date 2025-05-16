from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import app.keyboards as kb
from app.utils import extract_keywords
from app.db import get_plugins_by_tags_and_type

router = Router()

class SearchState(StatesGroup):
    waiting_for_query = State()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет!', reply_markup=kb.main)

@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('Здесь будет руководство по использованию бота', reply_markup=kb.main)

@router.message(F.text == 'Поиск плагинов')
async def search_plugins_handler(message: Message, state: FSMContext):
    await message.answer(
        "Введите описание плагина, который вы хотите найти.\n"
        "Пример: 'Бесплатный ревербератор для FL Studio'",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(SearchState.waiting_for_query)

@router.message(SearchState.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext):
    query = message.text
    plugin_type, tags = extract_keywords(query)

    if not plugin_type and not tags:
        await message.answer("Не удалось найти ключевые слова. Попробуйте уточнить.")
        return

    results = await get_plugins_by_tags_and_type(plugin_type, tags)

    if not results:
        await message.answer("Плагины не найдены.")
        await state.clear()
        return

    response = "Найденные плагины:\n\n"
    for name, description, link in results:
        response += f"📌 {name}\n{description}\nСсылка: {link}\n\n"

    await message.answer(response, reply_markup=kb.main)
    await state.clear()