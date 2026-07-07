from aiogram.fsm.state import State, StatesGroup


class Profile(StatesGroup):
    gender = State()
    age = State()
    height = State()
    weight = State()
    target_weight = State()
    activity = State()


class FoodEntry(StatesGroup):
    waiting_food_name = State()
    waiting_grams = State()
    waiting_manual_calories = State()


class WeightEntry(StatesGroup):
    waiting_weight = State()
