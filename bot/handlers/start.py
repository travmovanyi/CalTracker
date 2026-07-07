from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states import Profile
from bot.keyboards import gender_kb, activity_kb, main_menu_kb
from bot.calculations import ACTIVITY_LEVELS, calculate_daily_goal
from bot.database import upsert_user, get_user

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user:
        await message.answer(
            "З поверненням! 👋 Обери дію в меню нижче.",
            reply_markup=main_menu_kb()
        )
    else:
        await message.answer(
            "Привіт! 👋 Я допоможу рахувати калорії та відстежувати прогрес у схудненні.\n\n"
            "Спершу налаштуємо твій профіль. Яка у тебе стать?",
            reply_markup=gender_kb()
        )
        await state.set_state(Profile.gender)


@router.message(Command("profile"))
async def cmd_profile(message: Message, state: FSMContext):
    await message.answer("Оновимо профіль. Яка у тебе стать?", reply_markup=gender_kb())
    await state.set_state(Profile.gender)


@router.message(Profile.gender, F.text.in_(["Чоловіча", "Жіноча"]))
async def process_gender(message: Message, state: FSMContext):
    gender = "male" if message.text == "Чоловіча" else "female"
    await state.update_data(gender=gender)
    await message.answer("Скільки тобі повних років?", reply_markup=None)
    await state.set_state(Profile.age)


@router.message(Profile.gender)
async def process_gender_invalid(message: Message):
    await message.answer("Будь ласка, обери стать за допомогою кнопок нижче.", reply_markup=gender_kb())


@router.message(Profile.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text.isdigit() or not (10 <= int(message.text) <= 100):
        await message.answer("Введи вік числом, наприклад: 28")
        return
    await state.update_data(age=int(message.text))
    await message.answer("Який у тебе зріст у сантиметрах? Наприклад: 175")
    await state.set_state(Profile.height)


@router.message(Profile.height)
async def process_height(message: Message, state: FSMContext):
    try:
        height = float(message.text.replace(",", "."))
        assert 100 <= height <= 250
    except (ValueError, AssertionError):
        await message.answer("Введи зріст числом у см, наприклад: 175")
        return
    await state.update_data(height=height)
    await message.answer("Яка у тебе поточна вага в кг? Наприклад: 78.5")
    await state.set_state(Profile.weight)


@router.message(Profile.weight)
async def process_weight(message: Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
        assert 30 <= weight <= 300
    except (ValueError, AssertionError):
        await message.answer("Введи вагу числом у кг, наприклад: 78.5")
        return
    await state.update_data(weight=weight)
    await message.answer("Яку вагу хочеш мати як ціль (кг)? Наприклад: 70")
    await state.set_state(Profile.target_weight)


@router.message(Profile.target_weight)
async def process_target_weight(message: Message, state: FSMContext):
    try:
        target_weight = float(message.text.replace(",", "."))
        assert 30 <= target_weight <= 300
    except (ValueError, AssertionError):
        await message.answer("Введи цільову вагу числом у кг, наприклад: 70")
        return
    await state.update_data(target_weight=target_weight)
    await message.answer(
        "Який у тебе рівень фізичної активності?",
        reply_markup=activity_kb()
    )
    await state.set_state(Profile.activity)


@router.message(Profile.activity, F.text.in_(list(ACTIVITY_LEVELS.keys())))
async def process_activity(message: Message, state: FSMContext):
    data = await state.update_data(activity_label=message.text)
    activity_factor = ACTIVITY_LEVELS[message.text]

    result = calculate_daily_goal(
        gender=data["gender"],
        weight=data["weight"],
        height=data["height"],
        age=data["age"],
        target_weight=data["target_weight"],
        activity_factor=activity_factor,
    )

    upsert_user(
        user_id=message.from_user.id,
        gender=data["gender"],
        age=data["age"],
        height=data["height"],
        weight=data["weight"],
        target_weight=data["target_weight"],
        activity_factor=activity_factor,
        daily_goal=result["daily_goal"],
    )

    await message.answer(
        f"Готово! ✅\n\n"
        f"Базовий обмін речовин (BMR): {result['bmr']} ккал\n"
        f"Загальна витрата енергії (TDEE): {result['tdee']} ккал\n"
        f"Ціль: {result['goal_type']}\n\n"
        f"🎯 Твоя денна норма: {result['daily_goal']} ккал\n\n"
        f"Тепер можеш додавати прийоми їжі та відстежувати вагу через меню.",
        reply_markup=main_menu_kb()
    )
    await state.clear()


@router.message(Profile.activity)
async def process_activity_invalid(message: Message):
    await message.answer("Будь ласка, обери рівень активності кнопкою нижче.", reply_markup=activity_kb())


@router.message(F.text == "👤 Мій профіль")
async def show_profile(message: Message):
    user = get_user(message.from_user.id)
    if not user:
        await message.answer("Профіль ще не налаштовано. Напиши /start")
        return
    gender_ua = "Чоловіча" if user["gender"] == "male" else "Жіноча"
    await message.answer(
        f"👤 Твій профіль:\n\n"
        f"Стать: {gender_ua}\n"
        f"Вік: {user['age']}\n"
        f"Зріст: {user['height']} см\n"
        f"Поточна вага: {user['weight']} кг\n"
        f"Цільова вага: {user['target_weight']} кг\n"
        f"🎯 Денна норма: {user['daily_goal']} ккал\n\n"
        f"Щоб оновити профіль — напиши /profile"
    )
