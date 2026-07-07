from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from bot.calculations import ACTIVITY_LEVELS


def main_menu_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="🍽 Додати їжу")
    kb.button(text="📊 Сьогодні")
    kb.button(text="⚖️ Внести вагу")
    kb.button(text="📈 Графік ваги")
    kb.button(text="👤 Мій профіль")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)


def gender_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    kb.button(text="Чоловіча")
    kb.button(text="Жіноча")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


def activity_kb() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()
    for label in ACTIVITY_LEVELS.keys():
        kb.button(text=label)
    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True, one_time_keyboard=True)


def confirm_food_kb(found: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    if found:
        kb.button(text="✅ Так, це воно", callback_data="food_confirm_yes")
        kb.button(text="✏️ Ввести калорії вручну", callback_data="food_confirm_manual")
    else:
        kb.button(text="✏️ Ввести калорії вручну", callback_data="food_confirm_manual")
    kb.button(text="❌ Скасувати", callback_data="food_confirm_cancel")
    kb.adjust(1)
    return kb.as_markup()
