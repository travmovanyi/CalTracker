import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile

from bot.states import WeightEntry
from bot.keyboards import main_menu_kb
from bot.database import add_weight_entry, get_weight_history, get_user
from bot.calculations import calculate_daily_goal

router = Router()


@router.message(F.text == "⚖️ Внести вагу")
async def start_weight_entry(message: Message, state: FSMContext):
    await message.answer("Яка у тебе вага сьогодні (кг)? Наприклад: 76.4")
    await state.set_state(WeightEntry.waiting_weight)


@router.message(WeightEntry.waiting_weight)
async def process_weight_entry(message: Message, state: FSMContext):
    try:
        weight = float(message.text.replace(",", "."))
        assert 30 <= weight <= 300
    except (ValueError, AssertionError):
        await message.answer("Введи вагу числом у кг, наприклад: 76.4")
        return

    add_weight_entry(message.from_user.id, weight)
    await state.clear()

    user = get_user(message.from_user.id)
    text = f"Вагу {weight} кг занесено ✅"

    if user:
        result = calculate_daily_goal(
            gender=user["gender"], weight=weight, height=user["height"],
            age=user["age"], target_weight=user["target_weight"],
            activity_factor=user["activity_factor"]
        )
        text += f"\n\n🎯 Оновлена денна норма: {result['daily_goal']} ккал"
        diff = user["target_weight"] - weight
        if abs(diff) <= 0.5:
            text += "\n🎉 Ти досяг(-ла) цільової ваги!"

    await message.answer(text, reply_markup=main_menu_kb())


@router.message(F.text == "📈 Графік ваги")
async def show_weight_chart(message: Message):
    history = get_weight_history(message.from_user.id)
    if len(history) < 2:
        await message.answer(
            "Замало даних для графіка. Внеси вагу хоча б двічі в різні дні "
            "(кнопка «⚖️ Внести вагу»)."
        )
        return

    dates = [datetime.fromisoformat(h["log_date"]) for h in history]
    weights = [h["weight"] for h in history]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(dates, weights, marker="o", color="#2E86AB", linewidth=2)
    ax.set_title("Динаміка ваги")
    ax.set_xlabel("Дата")
    ax.set_ylabel("Вага, кг")
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    fig.autofmt_xdate()

    user = get_user(message.from_user.id)
    if user and user.get("target_weight"):
        ax.axhline(y=user["target_weight"], color="#A23B72", linestyle="--",
                    label=f"Ціль: {user['target_weight']} кг")
        ax.legend()

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)

    photo = BufferedInputFile(buf.read(), filename="weight_chart.png")
    await message.answer_photo(photo, caption=f"Записів: {len(history)}")
