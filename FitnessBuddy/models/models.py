"""
models/models.py

Thin data-access layer over SQLite. No ORM is used (per the project's
"use SQLite" requirement) — just plain sqlite3 with parameterized
queries to prevent SQL injection.
"""

import sqlite3
from datetime import date

from database.init_db import get_connection


# ---------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------
def create_user(name, age, gender, height, weight, goal, activity_level):
    conn = get_connection()
    try:
        cur = conn.execute(
            """INSERT INTO users (name, age, gender, height, weight, goal, activity_level)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, age, gender, height, weight, goal, activity_level),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user(user_id):
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_user(user_id, **fields):
    if not fields:
        return
    allowed = {"name", "age", "gender", "height", "weight", "goal", "activity_level"}
    fields = {k: v for k, v in fields.items() if k in allowed}
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]
    conn = get_connection()
    try:
        conn.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
        conn.commit()
    finally:
        conn.close()


def list_users():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


# ---------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------
def log_progress(user_id, weight=None, water_intake=None, workout_done=0, log_date=None):
    log_date = log_date or date.today().isoformat()
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM progress WHERE user_id = ? AND date = ?", (user_id, log_date)
        ).fetchone()
        if existing:
            conn.execute(
                """UPDATE progress
                   SET weight = COALESCE(?, weight),
                       water_intake = COALESCE(?, water_intake),
                       workout_done = ?
                   WHERE id = ?""",
                (weight, water_intake, workout_done, existing["id"]),
            )
        else:
            conn.execute(
                """INSERT INTO progress (user_id, weight, water_intake, workout_done, date)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, weight, water_intake, workout_done, log_date),
            )
        conn.commit()
    finally:
        conn.close()


def get_progress(user_id, limit=30):
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM progress WHERE user_id = ?
               ORDER BY date ASC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_weekly_summary(user_id):
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM progress WHERE user_id = ?
               ORDER BY date DESC LIMIT 7""",
            (user_id,),
        ).fetchall()
        rows = [dict(r) for r in rows][::-1]
        if not rows:
            return {
                "workouts_completed": 0,
                "avg_water": 0,
                "weight_change": 0,
                "days_logged": 0,
            }
        workouts = sum(1 for r in rows if r["workout_done"])
        waters = [r["water_intake"] for r in rows if r["water_intake"] is not None]
        weights = [r["weight"] for r in rows if r["weight"] is not None]
        weight_change = round(weights[-1] - weights[0], 2) if len(weights) >= 2 else 0
        return {
            "workouts_completed": workouts,
            "avg_water": round(sum(waters) / len(waters), 2) if waters else 0,
            "weight_change": weight_change,
            "days_logged": len(rows),
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------
def save_chat(user_id, question, response):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO chat_history (user_id, question, response) VALUES (?, ?, ?)",
            (user_id, question, response),
        )
        conn.commit()
    finally:
        conn.close()


def get_chat_history(user_id, limit=50):
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT * FROM chat_history WHERE user_id = ?
               ORDER BY timestamp ASC LIMIT ?""",
            (user_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
