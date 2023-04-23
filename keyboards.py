from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton


button_help = KeyboardButton('/help')
button_questions = KeyboardButton('/questions')
button_create = KeyboardButton('/create')

greet_kb = ReplyKeyboardMarkup(resize_keyboard=True).add(button_help,\
                                                        button_questions,\
                                                        button_create)


def generate_buttons(answer1, answer2):
    inline_btn_1 = InlineKeyboardButton(answer1, callback_data='button1')
    inline_btn_2 = InlineKeyboardButton(answer2, callback_data='button2')
    inline_kb = InlineKeyboardMarkup().add(inline_btn_1, inline_btn_2)
    return inline_kb
