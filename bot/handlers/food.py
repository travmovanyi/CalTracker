from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.states import FoodEntry
from bot.keyboards import confirm_food_kb, main_menu_kb
from bot.food_database import find_food
from bot.database import add_food_entry, get_today_food, get_user, delete_last_food_entry

router = Router()


@router.message(F.text == "🍽 Додати їжу")
async def start_food_entry(message: Message, state: FSMContext):
    await message.answer(
        "Напиши назву продукту або страви (наприклад: «куряче філе варене»)."
    )
    await state.set_state(FoodEntry.waiting_food_name)


@router.message(FoodEntry.waiting_food_name)
async def process_food_name(message: Message, state: FSMContext):
    name, data = find_food(message.text)
    await state.update_data(query=message.text, found_name=name, found_data=data)

    if data:
        kcal, protein, fat, carbs = data
        await message.answer(
            f"Знайшов у базі: «{name}»\n"
            f"На 100 г: {kcal} ккал, Б {protein} / Ж {fat} / В {carbs}\n\n"
            f"Це те, що ти шукаєш?",
            reply_markup=confirm_food_kb(found=True)
        )
    else:
        await message.answer(
            "Такого продукту немає в моїй базі. Можеш ввести калорійність вручну.",
            reply_markup=confirm_food_kb(found=False)
        )


@router.callback_query(F.data == "food_confirm_yes")
async def food_confirm_yes(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Скільки грам ти з'їв(-ла)? Наприклад: 150")
    await state.set_state(FoodEntry.waiting_grams)
    await callback.answer()


@router.callback_query(F.data == "food_confirm_manual")
async def food_confirm_manual(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "Введи калорійність порції одним числом (ккал), наприклад: 350"
    )
    await state.set_state(FoodEntry.waiting_manual_calories)
    await callback.answer()


@router.callback_query(F.data == "food_confirm_cancel")
async def food_confirm_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Скасовано.", reply_markup=main_menu_kb())
    await state.clear()
    await callback.answer()


@router.message(FoodEntry.waiting_grams)
async def process_grams(message: Message, state: FSMContext):
    try:
        grams = float(message.text.replace(",", "."))
        assert 1 <= grams <= 3000
    except (ValueError, AssertionError):
        await message.answer("Введи кількість грамів числом, наприклад: 150")
        return

    data = await state.get_data()
    kcal, protein, fat, carbs = data["found_data"]
    factor = grams / 100

    total_kcal = round(kcal * factor)
    total_protein = round(protein * factor, 1)
    total_fat = round(fat * factor, 1)
    total_carbs = round(carbs * factor, 1)

    add_food_entry(
        message.from_user.id, data["found_name"], grams,
        total_kcal, total_protein, total_fat, total_carbs
    )

    await message.answer(
        f"Додано: {data['found_name']} — {grams} г\n"
        f"🔥 {total_kcal} ккал | Б {total_protein} / Ж {total_fat} / В {total_carbs}",
        reply_markup=main_menu_kb()
    )
    await state.clear()
    await show_today_summary(message)


@router.message(FoodEntry.waiting_manual_calories)
async def process_manual_calories(message: Message, state: FSMContext):
    try:
        kcal = float(message.text.replace(",", "."))
        assert 1 <= kcal <= 5000
    except (ValueError, AssertionError):
        await message.answer("Введи калорійність числом, наприклад: 350")
        return

    data = await state.get_data()
    name = data.get("found_name") or data.get("query")

    add_food_entry(message.from_user.id, name, None, kcal, None, None, None)

    await message.answer(
        f"Додано: {name}\n🔥 {round(kcal)} ккал",
        reply_markup=main_menu_kb()
    )
    await state.clear()
    await show_today_summary(message)


@router.message(F.text == "📊 Сьогодні")
async def show_today_summary(message: Message):
    entries = get_today_food(message.from_user.id)
    user = get_user(message.from_user.id)
    goal = user["daily_goal"] if user else None

    if not entries:
        await message.answer("Сьогодні ще немає записів про їжу.")
        return

    total_kcal = sum(e["calories"] or 0 for e in entries)
    lines = [f"• {e['food_name']} — {round(e['calories'])} ккал" for e in entries]

    text = "📊 Сьогодні з'їдено:\n\n" + "\n".join(lines)
    text += f"\n\nВсього: {round(total_kcal)} ккал"
    if goal:
        remaining = goal - total_kcal
        text += f"\nНорма: {goal} ккал"
        if remaining >= 0:
            text += f"\n✅ Залишилось: {round(remaining)} ккал"
        else:
            text += f"\n⚠️ Перевищено на: {round(-remaining)} ккал"

    await message.answer(text)


@router.message(F.text == "❌ Видалити останній запис")
async def delete_last(message: Message):
    ok = delete_last_food_entry(message.from_user.id)
    if ok:
        await message.answer("Останній запис видалено.")
    else:
        await message.answer("Сьогодні ще немає записів для видалення.")
