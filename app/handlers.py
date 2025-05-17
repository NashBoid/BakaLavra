from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import app.keyboards as kb
from app.utils import extract_keywords, is_owner
from app.db import (
    get_all_tags, get_all_types, get_all_plugins, get_total_plugin_count,
    add_plugin, add_tag, add_type, get_plugins_by_tags_and_type
)

router = Router()

# --- FSM ---
class SearchPluginState(StatesGroup):
    waiting_for_query = State()

class AddPluginState(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()
    waiting_for_link = State()
    waiting_for_type = State()
    waiting_for_tags = State()

class AddTypeTagState(StatesGroup):
    waiting_for_type_name = State()
    waiting_for_tag_name = State()

class ViewPluginsState(StatesGroup):
    viewing = State()


# === ОСНОВНЫЕ КОМАНДЫ ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ === #

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('👋 Привет!', reply_markup=kb.main)

@router.message(Command('help'))
async def cmd_help(message: Message):
    await message.answer('ℹ️ Здесь будет руководство по использованию бота', reply_markup=kb.main)

@router.message(F.text == 'Поиск плагинов')
async def search_plugins_handler(message: Message, state: FSMContext):
    await message.answer(
        "Введите описание плагина, который вы хотите найти.\n"
        "Пример: 'Бесплатный ревербератор для FL Studio'",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(SearchPluginState.waiting_for_query)

@router.message(SearchPluginState.waiting_for_query)
async def process_search_query(message: Message, state: FSMContext):
    query = message.text
    plugin_type, tags = extract_keywords(query)

    results = await get_plugins_by_tags_and_type(plugin_type, tags)

    if not results:
        await message.answer("❌ Плагины не найдены.", reply_markup=kb.main)
        await state.clear()
        return

    response = "🔎 Найденные плагины:\n\n"
    for name, description, link in results:
        response += f"📌 {name}\n{description}\n🔗 {link}\n\n"

    await message.answer(response, reply_markup=kb.main)
    await state.clear()


# === АДМИН-ПАНЕЛЬ И КОМАНДЫ ТОЛЬКО ДЛЯ ВЛАДЕЛЬЦА === #

@router.message(Command('admin'))
async def cmd_admin(message: Message):
    if not is_owner(message.from_user.id):
        await message.answer("🚫 У вас нет доступа к админ-панели.", reply_markup=kb.main)
        return

    await message.answer("📘 Список команд админа:\n\n"
                         "🔹 /add_type — добавить тип\n"
                         "🔹 /add_tag — добавить тег\n"
                         "🔹 /add_plugin — добавить плагин\n"
                         "🔹 /list_types — посмотреть типы\n"
                         "🔹 /list_tags — посмотреть теги\n"
                         "🔹 /show_plugins — список плагинов\n"
                         "\nТеперь вы можете использовать клавиатуру для управления.",
                         reply_markup=kb.admin_menu)

@router.message(Command('admin_exit'))
async def cmd_admin_exit(message: Message):
    await message.answer("🚪 Вы вышли из меню администратора.", reply_markup=kb.main)


# --- Добавление типа ---
@router.message(Command('add_type'))
async def cmd_add_type(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        await message.answer("❌ У вас нет прав для добавления типов.", reply_markup=kb.admin_menu)
        return
    await message.answer("Введите название нового типа:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddTypeTagState.waiting_for_type_name)

@router.message(AddTypeTagState.waiting_for_type_name)
async def process_new_type(message: Message, state: FSMContext):
    type_name = message.text.strip()
    await add_type(type_name)
    await message.answer(f"✅ Тип '{type_name}' успешно добавлен!", reply_markup=kb.admin_menu)
    await state.clear()


# --- Добавление тега ---
@router.message(Command('add_tag'))
async def cmd_add_tag(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        await message.answer("❌ У вас нет прав для добавления тегов.", reply_markup=kb.admin_menu)
        return
    await message.answer("Введите название нового тега:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddTypeTagState.waiting_for_tag_name)

@router.message(AddTypeTagState.waiting_for_tag_name)
async def process_new_tag(message: Message, state: FSMContext):
    tag_name = message.text.strip()
    await add_tag(tag_name)
    await message.answer(f"✅ Тег '{tag_name}' успешно добавлен!", reply_markup=kb.admin_menu)
    await state.clear()


# --- Добавление плагина ---
@router.message(Command('add_plugin'))
async def add_plugin_start(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        await message.answer("❌ У вас нет прав для добавления плагинов.", reply_markup=kb.admin_menu)
        return
    await message.answer("Введите название плагина:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(AddPluginState.waiting_for_title)

@router.message(AddPluginState.waiting_for_title)
async def add_plugin_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите описание плагина:")
    await state.set_state(AddPluginState.waiting_for_description)

@router.message(AddPluginState.waiting_for_description)
async def add_plugin_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите ссылку для скачивания:")
    await state.set_state(AddPluginState.waiting_for_link)

@router.message(AddPluginState.waiting_for_link)
async def add_plugin_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text)

    types = await get_all_types()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t[1], callback_data=f"type_{t[0]}")] for t in types
    ] + [[InlineKeyboardButton(text="➕ Добавить новый тип", callback_data="type_new")]])

    await message.answer("Выберите тип плагина или добавьте новый:", reply_markup=keyboard)
    await state.set_state(AddPluginState.waiting_for_type)

@router.callback_query(AddPluginState.waiting_for_type)
async def add_plugin_type(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data
    if data == "type_new":
        await callback_query.message.answer("Введите название нового типа:")
        await state.set_state(AddTypeTagState.waiting_for_type_name)
    else:
        type_id = int(data.split('_')[1])
        await state.update_data(type_id=type_id)
        tags = await get_all_tags()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t[1], callback_data=f"tag_{t[0]}")] for t in tags
        ] + [[InlineKeyboardButton(text="➕ Добавить новый тег", callback_data="tag_new")]])
        await callback_query.message.answer("Выберите теги или добавьте новые:", reply_markup=keyboard)
        await state.set_state(AddPluginState.waiting_for_tags)

@router.message(AddTypeTagState.waiting_for_type_name)
async def add_new_type(message: Message, state: FSMContext):
    type_name = message.text
    type_id = await add_type(type_name)
    await state.update_data(type_id=type_id)
    tags = await get_all_tags()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t[1], callback_data=f"tag_{t[0]}")] for t in tags
    ] + [[InlineKeyboardButton(text="➕ Добавить новый тег", callback_data="tag_new")]])
    await message.answer("Выберите теги или добавьте новые:", reply_markup=keyboard)
    await state.set_state(AddPluginState.waiting_for_tags)

@router.callback_query(AddPluginState.waiting_for_tags)
async def add_plugin_tags(callback_query: CallbackQuery, state: FSMContext):
    data = callback_query.data
    if data == "tag_new":
        await callback_query.message.answer("Введите название нового тега:")
        await state.set_state(AddTypeTagState.waiting_for_tag_name)
    else:
        tag_id = int(data.split('_')[1])
        data = await state.get_data()
        tags = data.get("tags", [])
        tags.append(tag_id)
        await state.update_data(tags=tags)
        await callback_query.message.answer("📌 Продолжайте выбор или нажмите /done")

@router.message(AddTypeTagState.waiting_for_tag_name)
async def add_new_tag(message: Message, state: FSMContext):
    tag_name = message.text
    tag_id = await add_tag(tag_name)
    data = await state.get_data()
    tags = data.get("tags", [])
    tags.append(tag_id)
    await state.update_data(tags=tags)
    await message.answer("📌 Тег добавлен. Продолжайте выбор или нажмите /done")

@router.message(Command('done'))
async def finish_add_plugin(message: Message, state: FSMContext):
    data = await state.get_data()
    plugin_id = await add_plugin(
        title=data["title"],
        description=data["description"],
        link=data["link"],
        type_id=data["type_id"],
        tag_ids=data.get("tags", [])
    )
    await message.answer(f"📌 Плагин '{data['title']}' успешно добавлен!", reply_markup=kb.admin_menu)
    await state.clear()


# --- Просмотр типов и тегов ---
@router.message(Command('list_types'))
async def list_types(message: Message):
    types = await get_all_types()
    text = "📌 Доступные типы:\n\n" + "\n".join([f"{t[0]}. {t[1]}" for t in types])
    await message.answer(text, reply_markup=kb.admin_menu)

@router.message(Command('list_tags'))
async def list_tags(message: Message):
    tags = await get_all_tags()
    text = "📌 Доступные теги:\n\n" + "\n".join([f"{t[0]}. {t[1]}" for t in tags])
    await message.answer(text, reply_markup=kb.admin_menu)


# --- Просмотр списка плагинов ---
def get_pagination_keyboard(current_page: int, total_pages: int):
    buttons = []

    if current_page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"page_{current_page - 1}"))
    else:
        buttons.append(InlineKeyboardButton(text="🚫", callback_data="no_action"))

    buttons.append(InlineKeyboardButton(text=f"{current_page + 1}/{total_pages}", callback_data="page_info"))

    if current_page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"page_{current_page + 1}"))
    else:
        buttons.append(InlineKeyboardButton(text="🚫", callback_data="no_action"))

    return InlineKeyboardMarkup(inline_keyboard=[buttons])

@router.message(Command('show_plugins'))
async def cmd_show_plugins(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        await message.answer("❌ У вас нет прав для просмотра плагинов.", reply_markup=kb.admin_menu)
        return

    total_plugins = await get_total_plugin_count()
    if total_plugins == 0:
        await message.answer("⚠️ База плагинов пуста.", reply_markup=kb.admin_menu)
        return

    # Сохраняем общее количество плагинов
    await state.update_data(page=0, total_plugins=total_plugins)

    plugins = await get_all_plugins(limit=5, offset=0)
    text = "📁 Список плагинов:\n\n" + "\n".join([f"{p[0]}. {p[1]}" for p in plugins])

    total_pages = (total_plugins + 4) // 5
    keyboard = get_pagination_keyboard(current_page=0, total_pages=total_pages)
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(ViewPluginsState.viewing)

@router.callback_query(ViewPluginsState.viewing)
async def navigate_plugins(callback_query: CallbackQuery, state: FSMContext):
    if callback_query.data.startswith("page_"):
        current_page = int(callback_query.data.split("_")[1])
        data = await state.get_data()
        total_plugins = data["total_plugins"]

        plugins = await get_all_plugins(limit=5, offset=current_page * 5)
        text = "📁 Список плагинов:\n\n" + "\n".join([f"{p[0]}. {p[1]}" for p in plugins])

        total_pages = (total_plugins + 4) // 5
        keyboard = get_pagination_keyboard(current_page, total_pages)
        await callback_query.message.edit_text(text, reply_markup=keyboard)
        await state.update_data(page=current_page)