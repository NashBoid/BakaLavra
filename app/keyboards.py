from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Поиск плагинов')],
                                     [KeyboardButton(text='История поиска')]
                                     ], resize_keyboard=True,
                           input_field_placeholder='Выберите пункт меню...')

# Клавиатура администратора
admin_menu = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='/add_type')],                 # Добавить тип
    [KeyboardButton(text='/add_tag')],                  # Добавить тег
    [KeyboardButton(text='/add_plugin')],               # Добавить плагин
    [KeyboardButton(text='/list_types')],               # Просмотр типов
    [KeyboardButton(text='/list_tags')],                # Просмотр тегов
    [KeyboardButton(text='/show_plugins')],              # Просмотр плагинов
    [KeyboardButton(text='/admin_exit')],               # Выход из меню админа
], resize_keyboard=True, input_field_placeholder='Админ-панель')