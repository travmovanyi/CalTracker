import os

# Встав сюди токен свого бота, отриманий від @BotFather у Telegram,
# або задай змінну середовища BOT_TOKEN
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВСТАВ_СЮДИ_СВІЙ_ТОКЕН")

DB_PATH = os.getenv(
    "DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "calorie_bot.db")
)
