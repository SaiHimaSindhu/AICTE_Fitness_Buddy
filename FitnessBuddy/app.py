"""
app.py — Fitness Buddy

Entry point for the Flask application. Wires together the templates,
the SQLite data layer (models/models.py) and the IBM Granite /
watsonx.ai service (services/granite_service.py).

Run:
    python app.py
"""

import os
from datetime import date

from flask import Flask, render_template, request, jsonify, session, redirect, url_for

from config import Config
from database.init_db import init_db
from models import models
from services import granite_service

app = Flask(__name__)
app.config.from_object(Config)


# Ensure the database exists (with schema + sample data) before the
# first request is served.
with app.app_context():
    init_db(seed_sample_data=True)


def _require_user():
    """Returns the active user's id from session, or None."""
    return session.get("user_id")


def _error(message, status=400):
    return jsonify({"success": False, "error": message}), status


# =====================================================================
# PAGE ROUTES (server-rendered HTML)
# =====================================================================
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")


@app.route("/dashboard")
def dashboard_page():
    user_id = _require_user()
    if not user_id:
        return redirect(url_for("register_page"))
    user = models.get_user(user_id)
    if not user:
        session.pop("user_id", None)
        return redirect(url_for("register_page"))
    summary = models.get_weekly_summary(user_id)
    return render_template("dashboard.html", user=user, summary=summary)


@app.route("/workout")
def workout_page():
    user_id = _require_user()
    if not user_id:
        return redirect(url_for("register_page"))
    return render_template("workout.html", user=models.get_user(user_id))


@app.route("/nutrition")
def nutrition_page():
    user_id = _require_user()
    if not user_id:
        return redirect(url_for("register_page"))
    return render_template("nutrition.html", user=models.get_user(user_id))


@app.route("/progress")
def progress_page():
    user_id = _require_user()
    if not user_id:
        return redirect(url_for("register_page"))
    return render_template("progress.html", user=models.get_user(user_id))


@app.route("/chat")
def chat_page():
    user_id = _require_user()
    if not user_id:
        return redirect(url_for("register_page"))
    history = models.get_chat_history(user_id)
    return render_template("chat.html", user=models.get_user(user_id), history=history)


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("index"))


# =====================================================================
# API — Profile
# =====================================================================
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or request.form
    required = ["name", "age", "gender", "height", "weight", "goal", "activity_level"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return _error(f"Missing required fields: {', '.join(missing)}")

    try:
        user_id = models.create_user(
            name=str(data["name"]).strip(),
            age=int(data["age"]),
            gender=str(data["gender"]).lower(),
            height=float(data["height"]),
            weight=float(data["weight"]),
            goal=str(data["goal"]).lower(),
            activity_level=str(data["activity_level"]).lower(),
        )
    except (ValueError, TypeError):
        return _error("Age, height and weight must be valid numbers.")

    session["user_id"] = user_id
    session.permanent = True
    return jsonify({"success": True, "user_id": user_id, "redirect": url_for("dashboard_page")})


@app.route("/api/user/<int:user_id>", methods=["GET"])
def api_get_user(user_id):
    user = models.get_user(user_id)
    if not user:
        return _error("User not found", 404)
    return jsonify({"success": True, "user": user})


@app.route("/api/user/<int:user_id>", methods=["PUT"])
def api_update_user(user_id):
    data = request.get_json(silent=True) or {}
    models.update_user(user_id, **data)
    return jsonify({"success": True, "user": models.get_user(user_id)})


# =====================================================================
# API — AI Fitness Coach
# =====================================================================
@app.route("/api/workout/plan", methods=["POST"])
def api_workout_plan():
    user_id = _require_user()
    if not user_id:
        return _error("Not logged in", 401)
    user = models.get_user(user_id)
    plan = granite_service.generate_workout_plan(user)
    return jsonify({"success": True, "plan": plan})


@app.route("/api/workout/home", methods=["POST"])
def api_home_workout():
    user_id = _require_user()
    if not user_id:
        return _error("Not logged in", 401)
    user = models.get_user(user_id)
    workout = granite_service.generate_home_workout(user)
    return jsonify({"success": True, "workout": workout})


@app.route("/api/workout/tip", methods=["GET"])
def api_fitness_tip():
    return jsonify({"success": True, "tip": granite_service.generate_fitness_tip()})


# =====================================================================
# API — Nutrition Assistant
# =====================================================================
@app.route("/api/nutrition/plan", methods=["POST"])
def api_nutrition_plan():
    user_id = _require_user()
    if not user_id:
        return _error("Not logged in", 401)
    user = models.get_user(user_id)
    result = granite_service.generate_nutrition_plan(user)
    return jsonify({"success": True, **result})


# =====================================================================
# API — Daily Motivation
# =====================================================================
@app.route("/api/motivation", methods=["GET"])
def api_motivation():
    return jsonify(
        {
            "success": True,
            "quote": granite_service.generate_motivation(),
            "habit_tip": granite_service.generate_habit_tip(),
        }
    )


# =====================================================================
# API — Progress Tracking
# =====================================================================
@app.route("/api/progress", methods=["POST"])
def api_log_progress():
    user_id = _require_user()
    if not user_id:
        return _error("Not logged in", 401)
    data = request.get_json(silent=True) or {}
    try:
        weight = float(data["weight"]) if data.get("weight") not in (None, "") else None
        water = float(data["water_intake"]) if data.get("water_intake") not in (None, "") else None
    except (ValueError, TypeError):
        return _error("weight/water_intake must be numbers")
    workout_done = 1 if data.get("workout_done") else 0
    log_date = data.get("date") or date.today().isoformat()

    models.log_progress(user_id, weight=weight, water_intake=water,
                         workout_done=workout_done, log_date=log_date)

    if weight is not None:
        models.update_user(user_id, weight=weight)

    return jsonify({"success": True})


@app.route("/api/progress/<int:user_id>", methods=["GET"])
def api_get_progress(user_id):
    limit = request.args.get("limit", 30, type=int)
    rows = models.get_progress(user_id, limit=limit)
    summary = models.get_weekly_summary(user_id)
    return jsonify({"success": True, "progress": rows, "summary": summary})


# =====================================================================
# API — AI Chat Assistant
# =====================================================================
@app.route("/api/chat", methods=["POST"])
def api_chat():
    user_id = _require_user()
    if not user_id:
        return _error("Not logged in", 401)
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return _error("question is required")

    user = models.get_user(user_id)
    history = models.get_chat_history(user_id)
    response = granite_service.chat_with_coach(user, question, history=history)
    models.save_chat(user_id, question, response)
    return jsonify({"success": True, "response": response})


@app.route("/api/chat/history/<int:user_id>", methods=["GET"])
def api_chat_history(user_id):
    return jsonify({"success": True, "history": models.get_chat_history(user_id)})


# =====================================================================
# Error handlers
# =====================================================================
@app.errorhandler(404)
def not_found(e):
    return render_template("index.html"), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"success": False, "error": "Internal server error. Please try again."}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", True))
