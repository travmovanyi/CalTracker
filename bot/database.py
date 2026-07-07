import sqlite3
from datetime import date
from contextlib import contextmanager

from bot.config import DB_PATH


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                gender TEXT,
                age INTEGER,
                height REAL,
                weight REAL,
                target_weight REAL,
                activity_factor REAL,
                daily_goal REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS food_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                log_date TEXT,
                food_name TEXT,
                grams REAL,
                calories REAL,
                protein REAL,
                fat REAL,
                carbs REAL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS weight_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                log_date TEXT,
                weight REAL
            )
        """)


def upsert_user(user_id, gender, age, height, weight, target_weight, activity_factor, daily_goal):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO users (user_id, gender, age, height, weight, target_weight, activity_factor, daily_goal)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                gender=excluded.gender,
                age=excluded.age,
                height=excluded.height,
                weight=excluded.weight,
                target_weight=excluded.target_weight,
                activity_factor=excluded.activity_factor,
                daily_goal=excluded.daily_goal
        """, (user_id, gender, age, height, weight, target_weight, activity_factor, daily_goal))


def get_user(user_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        return dict(row) if row else None


def add_food_entry(user_id, food_name, grams, calories, protein, fat, carbs):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO food_log (user_id, log_date, food_name, grams, calories, protein, fat, carbs)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, date.today().isoformat(), food_name, grams, calories, protein, fat, carbs))


def get_today_food(user_id):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT * FROM food_log WHERE user_id=? AND log_date=? ORDER BY id
        """, (user_id, date.today().isoformat())).fetchall()
        return [dict(r) for r in rows]


def delete_last_food_entry(user_id):
    with get_conn() as conn:
        row = conn.execute("""
            SELECT id FROM food_log WHERE user_id=? AND log_date=? ORDER BY id DESC LIMIT 1
        """, (user_id, date.today().isoformat())).fetchone()
        if row:
            conn.execute("DELETE FROM food_log WHERE id=?", (row["id"],))
            return True
        return False


def add_weight_entry(user_id, weight):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO weight_log (user_id, log_date, weight) VALUES (?, ?, ?)
        """, (user_id, date.today().isoformat(), weight))
        conn.execute("UPDATE users SET weight=? WHERE user_id=?", (weight, user_id))


def get_weight_history(user_id, limit=60):
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT log_date, weight FROM weight_log WHERE user_id=?
            ORDER BY log_date ASC LIMIT ?
        """, (user_id, limit)).fetchall()
        return [dict(r) for r in rows]
