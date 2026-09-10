"""
services/granite_service.py

Integration layer for IBM Granite foundation models served through
IBM watsonx.ai.

Flow:
    1. Exchange the IBM Cloud IAM API key for a short-lived bearer
       token (cached until it expires).
    2. Call the watsonx.ai `text/generation` REST endpoint with the
       Granite model id + a task-specific prompt.
    3. Return the generated text to the caller.

If WATSONX_API_KEY / WATSONX_PROJECT_ID are not configured (or the
IBM Cloud call fails for any reason), the service transparently falls
back to a small local rule-based generator (`_mock_*` functions) so
the rest of the application keeps working — this is controlled by
Config.USE_MOCK_AI ("auto" = mock only when creds are missing / call
fails, "true" = always mock, "false" = never mock, raise on failure).
"""

import random
import time

import requests

from config import Config

_token_cache = {"access_token": None, "expires_at": 0}


# ---------------------------------------------------------------------
# IAM auth
# ---------------------------------------------------------------------
def _get_iam_token():
    now = time.time()
    if _token_cache["access_token"] and now < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    resp = requests.post(
        Config.WATSONX_IAM_URL,
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": Config.WATSONX_API_KEY,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + int(data.get("expires_in", 3600))
    return _token_cache["access_token"]


def _credentials_configured():
    return bool(Config.WATSONX_API_KEY and Config.WATSONX_PROJECT_ID)


def _should_mock():
    if Config.USE_MOCK_AI == "true":
        return True
    if Config.USE_MOCK_AI == "false":
        return False
    # "auto"
    return not _credentials_configured()


# ---------------------------------------------------------------------
# Core Granite call
# ---------------------------------------------------------------------
def call_granite(prompt, max_new_tokens=350, temperature=0.7):
    """
    Sends `prompt` to the IBM Granite model via watsonx.ai and returns
    the generated text (str). Falls back to a mock response on error
    or when credentials are not configured, unless
    Config.USE_MOCK_AI == "false" (in which case errors are raised).
    """
    if _should_mock():
        return None  # caller decides which mock generator to use

    try:
        token = _get_iam_token()
        url = f"{Config.WATSONX_URL}/ml/v1/text/generation?version={Config.WATSONX_VERSION}"
        payload = {
            "model_id": Config.GRANITE_MODEL_ID,
            "project_id": Config.WATSONX_PROJECT_ID,
            "input": prompt,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "repetition_penalty": 1.1,
            },
        }
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        if results:
            return results[0].get("generated_text", "").strip()
        return ""
    except Exception as exc:  # noqa: BLE001
        if Config.USE_MOCK_AI == "false":
            raise
        print(f"[granite_service] Falling back to mock AI due to error: {exc}")
        return None


# ---------------------------------------------------------------------
# Public, task-specific helpers
# Each one builds a prompt tailored to the task, calls Granite, and
# supplies a sensible mock fallback so the feature always works.
# ---------------------------------------------------------------------
def generate_workout_plan(user):
    prompt = (
        "You are Fitness Buddy, an encouraging certified personal trainer.\n"
        f"Client profile: {user['age']}-year-old {user['gender']}, "
        f"{user['height']}cm, {user['weight']}kg, goal: {user['goal']}, "
        f"activity level: {user['activity_level']}.\n"
        "Write a personalized 7-day home workout plan for this client. "
        "For each day, give the workout focus and 3-5 exercises with sets/reps. "
        "Keep it realistic for their activity level. Format with clear headings."
    )
    text = call_granite(prompt, max_new_tokens=600)
    return text if text else _mock_workout_plan(user)


def generate_home_workout(user):
    prompt = (
        f"Suggest a 20-30 minute equipment-free home workout for a "
        f"{user['activity_level']} activity {user['goal'].replace('_', ' ')} client. "
        "List exercises with sets and reps."
    )
    text = call_granite(prompt, max_new_tokens=300)
    return text if text else _mock_home_workout(user)


def generate_fitness_tip(user=None):
    prompt = "Give one short, specific, actionable fitness tip (2-3 sentences)."
    text = call_granite(prompt, max_new_tokens=100)
    return text if text else random.choice(_MOCK_FITNESS_TIPS)


def generate_nutrition_plan(user):
    calorie_target = _estimate_calories(user)
    prompt = (
        "You are a certified nutrition coach.\n"
        f"Client: {user['age']}-year-old {user['gender']}, {user['height']}cm, "
        f"{user['weight']}kg, goal: {user['goal']}, activity level: {user['activity_level']}. "
        f"Estimated daily calorie target: {calorie_target} kcal.\n"
        "Suggest a full day of healthy meals: breakfast, lunch, dinner, and two snacks. "
        "Keep portions realistic and include an approximate calorie count for each meal."
    )
    text = call_granite(prompt, max_new_tokens=500)
    return {
        "calorie_target": calorie_target,
        "plan": text if text else _mock_nutrition_plan(user, calorie_target),
    }


def generate_motivation():
    prompt = "Write one short, original motivational fitness quote (max 25 words)."
    text = call_granite(prompt, max_new_tokens=60)
    return text if text else random.choice(_MOCK_QUOTES)


def generate_habit_tip():
    prompt = "Give one short, practical tip for building a lasting fitness habit."
    text = call_granite(prompt, max_new_tokens=100)
    return text if text else random.choice(_MOCK_HABIT_TIPS)


def chat_with_coach(user, question, history=None):
    history_text = ""
    if history:
        for h in history[-5:]:
            history_text += f"User: {h['question']}\nCoach: {h['response']}\n"

    profile_line = ""
    if user:
        profile_line = (
            f"Client profile: {user['age']}yo {user['gender']}, {user['height']}cm, "
            f"{user['weight']}kg, goal: {user['goal']}, activity: {user['activity_level']}.\n"
        )

    prompt = (
        "You are Fitness Buddy, a friendly, knowledgeable AI fitness coach. "
        "Answer the client's question about workouts, diet, fitness, or motivation "
        "clearly and concisely. Do not give medical diagnoses; suggest seeing a "
        "doctor for medical concerns.\n"
        f"{profile_line}{history_text}User: {question}\nCoach:"
    )
    text = call_granite(prompt, max_new_tokens=300)
    return text if text else _mock_chat_response(question)


# ---------------------------------------------------------------------
# Calorie estimate (Mifflin-St Jeor) — used to ground the nutrition prompt
# ---------------------------------------------------------------------
def _estimate_calories(user):
    weight = float(user["weight"])
    height = float(user["height"])
    age = int(user["age"])
    gender = user["gender"].lower()

    if gender == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    tdee = bmr * activity_multipliers.get(user["activity_level"], 1.4)

    goal = user["goal"]
    if goal == "weight_loss":
        tdee -= 400
    elif goal == "muscle_gain":
        tdee += 300

    return int(round(tdee / 10.0) * 10)


# ---------------------------------------------------------------------
# Mock fallback generators (no external API calls)
# ---------------------------------------------------------------------
_MOCK_QUOTES = [
    "Progress, not perfection — every rep counts.",
    "Your only competition is who you were yesterday.",
    "Small steps daily lead to big results yearly.",
    "Discipline is choosing what you want most over what you want now.",
    "The body achieves what the mind believes.",
]

_MOCK_FITNESS_TIPS = [
    "Warm up for 5-10 minutes before any workout to reduce injury risk.",
    "Prioritize sleep — muscle recovery happens mostly while you rest.",
    "Progressive overload (a little more weight or reps each week) drives real gains.",
    "Stay hydrated: dehydration reduces strength and endurance significantly.",
    "Consistency beats intensity — a moderate workout you'll repeat beats a brutal one you'll skip.",
]

_MOCK_HABIT_TIPS = [
    "Stack your workout onto an existing habit, like right after brushing your teeth.",
    "Track streaks, not perfection — missing one day is fine, missing two starts a new habit.",
    "Prep your gym clothes the night before to remove decision friction.",
    "Set a specific time, not just 'sometime today' — vague plans get skipped.",
]


def _mock_workout_plan(user):
    goal = user["goal"]
    level = user["activity_level"]
    day_focus = {
        1: "Full Body Strength",
        2: "Cardio & Core",
        3: "Active Recovery / Mobility",
        4: "Upper Body Strength",
        5: "Lower Body Strength",
        6: "HIIT & Conditioning",
        7: "Rest / Light Walk",
    }
    lines = [f"7-Day Home Workout Plan (Goal: {goal.replace('_',' ').title()}, Level: {level.title()})\n"]
    exercises_by_focus = {
        "Full Body Strength": ["Bodyweight Squats 3x15", "Push-ups 3x10-15", "Glute Bridges 3x15", "Plank 3x30s"],
        "Cardio & Core": ["Jumping Jacks 4x30s", "Mountain Climbers 3x20", "Bicycle Crunches 3x20", "High Knees 3x30s"],
        "Active Recovery / Mobility": ["Light Walk 20min", "Full Body Stretch 10min", "Cat-Cow 2x10", "Hip Flexor Stretch 2x30s/side"],
        "Upper Body Strength": ["Push-ups 3x12", "Tricep Dips 3x12", "Superman Raises 3x15", "Plank Shoulder Taps 3x20"],
        "Lower Body Strength": ["Lunges 3x12/leg", "Wall Sit 3x30s", "Calf Raises 3x20", "Squat Pulses 3x15"],
        "HIIT & Conditioning": ["Burpees 4x10", "Jump Squats 4x12", "Plank Jacks 4x20", "Sprint in Place 4x30s"],
        "Rest / Light Walk": ["Gentle Walk 15-20min", "Deep Breathing 5min", "Full Body Stretch 10min"],
    }
    for day, focus in day_focus.items():
        lines.append(f"Day {day} — {focus}:")
        for ex in exercises_by_focus[focus]:
            lines.append(f"  • {ex}")
        lines.append("")
    return "\n".join(lines)


def _mock_home_workout(user):
    return (
        "20-Minute No-Equipment Home Workout:\n"
        "  • Jumping Jacks — 3 x 30s\n"
        "  • Bodyweight Squats — 3 x 15\n"
        "  • Push-ups (knee variation if needed) — 3 x 10\n"
        "  • Plank — 3 x 30s\n"
        "  • Lunges — 3 x 12 per leg\n"
        "  • Cool-down stretch — 3 minutes"
    )


def _mock_nutrition_plan(user, calorie_target):
    return (
        f"Daily Meal Plan (~{calorie_target} kcal):\n\n"
        "Breakfast (~350 kcal): Oatmeal with banana, a spoon of peanut butter, and a boiled egg.\n\n"
        "Mid-morning Snack (~120 kcal): Greek yogurt with a handful of berries.\n\n"
        "Lunch (~450 kcal): Grilled chicken or paneer, brown rice, and a mixed vegetable salad.\n\n"
        "Afternoon Snack (~150 kcal): A small handful of mixed nuts and an apple.\n\n"
        "Dinner (~400 kcal): Grilled fish or tofu, steamed vegetables, and a small sweet potato.\n\n"
        "Tip: Drink at least 2-3 liters of water throughout the day and space protein across meals."
    )


def _mock_chat_response(question):
    q = question.lower()
    if any(k in q for k in ["water", "hydrat"]):
        return "Aim for about 2-3 liters of water a day, and more if you're sweating a lot during workouts."
    if any(k in q for k in ["weight loss", "lose weight", "fat loss"]):
        return "Weight loss mainly comes from a modest calorie deficit combined with regular strength and cardio training. Aim for 0.3-0.5kg loss per week for a sustainable pace."
    if any(k in q for k in ["muscle", "gain", "bulk"]):
        return "For muscle gain, eat slightly above maintenance calories with enough protein (about 1.6-2.2g per kg bodyweight) and train with progressive overload 3-5 times a week."
    if any(k in q for k in ["motivat", "lazy", "give up", "tired"]):
        return random.choice(_MOCK_QUOTES) + " Start with just 10 minutes today — momentum builds from small wins."
    if any(k in q for k in ["diet", "eat", "food", "meal", "nutrition"]):
        return "Focus on whole foods: lean protein, vegetables, whole grains, and healthy fats. Keep processed sugar and fried foods occasional rather than daily."
    if any(k in q for k in ["workout", "exercise", "train", "gym"]):
        return "A balanced week mixes strength training (2-4x), cardio (1-3x), and at least one rest or mobility day. Adjust volume to your current fitness level."
    return (
        "Great question! In general, consistency with balanced training, adequate protein, "
        "sleep, and hydration is what drives most fitness progress. Could you tell me a bit "
        "more about your specific goal so I can tailor my advice?"
    )
