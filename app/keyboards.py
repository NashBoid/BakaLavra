from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Поиск плагинов')],
                                     [KeyboardButton(text='История поиска')]
                                     ], resize_keyboard=True,
                           input_field_placeholder='Выберите пункт меню...')