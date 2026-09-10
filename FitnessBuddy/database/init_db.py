"""
database/init_db.py

Creates database.db from schema.sql and (optionally) seeds it with a
sample user + progress history so the dashboard/charts have something
to show immediately after a fresh clone.

Run directly:
    python database/init_db.py
Or it is called automatically by app.py on first startup.
"""

import os
import sqlite3
from datetime import date, timedelta

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(BASE_DIR, "database.db")
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(seed_sample_data=True):
    fresh = not os.path.exists(DB_PATH)
    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        conn.executescript(f.read())
    conn.commit()

    if fresh and seed_sample_data:
        _seed_sample_data(conn)

    conn.close()
    print(f"[Fitness Buddy] Database ready at: {DB_PATH}")


def _seed_sample_data(conn):
    """Insert one demo user + two weeks of progress logs."""
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO users (name, age, gender, height, weight, goal, activity_level)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("Demo User", 26, "female", 165.0, 68.0, "weight_loss", "moderate"),
    )
    user_id = cur.lastrowid

    today = date.today()
    start_weight = 68.0
    for i in range(14, 0, -1):
        day = today - timedelta(days=i)
        weight = round(start_weight - (14 - i) * 0.08, 1)
        water = round(1.5 + (i % 4) * 0.3, 1)
        workout_done = 1 if i % 3 != 0 else 0
        cur.execute(
            """INSERT INTO progress (user_id, weight, water_intake, workout_done, date)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, weight, water, workout_done, day.isoformat()),
        )

    cur.execute(
        """INSERT INTO chat_history (user_id, question, response)
           VALUES (?, ?, ?)""",
        (
            user_id,
            "How much water should I drink daily?",
            "Aim for roughly 2-3 liters a day, more if you're training hard or it's hot out. "
            "Sip steadily through the day rather than chugging it all at once.",
        ),
    )
    conn.commit()
    print(f"[Fitness Buddy] Seeded sample user_id={user_id} with 14 days of progress data.")


if __name__ == "__main__":
    if os.path.exists(DB_PATH):
        answer = input(f"{DB_PATH} already exists. Recreate it? (y/N): ")
        if answer.lower() == "y":
            os.remove(DB_PATH)
            init_db()
        else:
            print("Left existing database untouched.")
    else:
        init_db()
