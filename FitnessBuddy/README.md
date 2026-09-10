# 🏋️ Fitness Buddy

**Fitness Buddy** is an AI-powered virtual fitness coach that gives personalized
workout plans, nutrition guidance, motivational tips, and habit-building
support — backed by the **IBM Granite** foundation model running on
**IBM watsonx.ai**, with a **Python Flask** backend, a responsive
**HTML/CSS/JavaScript (Bootstrap)** frontend, and a **SQLite** database.

---

## ✨ Features

| Module | What it does |
|---|---|
| **User Profile** | Create a profile with name, age, gender, height, weight, goal, activity level |
| **AI Fitness Coach** | 7-day workout plans, quick home workouts, fitness tips (IBM Granite) |
| **Nutrition Assistant** | Daily meal plan (breakfast/lunch/dinner/snacks) + calorie target |
| **Daily Motivation** | AI-generated motivational quotes + habit-building tips |
| **Progress Tracking** | Log weight / water intake / workout completion, view charts & weekly summary |
| **AI Chat Assistant** | Free-form chat about workouts, diet, fitness, and motivation |

The app works **even without IBM Cloud credentials** — a built-in mock AI
layer keeps every feature functional for local development, demos, or
grading. Add real watsonx.ai credentials any time to switch to live Granite
responses (see below).

---

## 🗂️ Project Structure

```
FitnessBuddy/
│
├── app.py                     # Flask app & all routes/APIs
├── config.py                  # Configuration (env vars, watsonx settings)
├── requirements.txt
├── README.md
├── .env.example                # Copy to .env and fill in your credentials
├── database.db                 # Created automatically on first run
│
├── database/
│   ├── schema.sql              # Table definitions (users, progress, chat_history)
│   └── init_db.py              # Creates DB + seeds sample data
│
├── models/
│   └── models.py                # SQLite data-access functions
│
├── services/
│   └── granite_service.py       # IBM Granite / watsonx.ai integration + mock fallback
│
├── static/
│   ├── css/style.css
│   ├── js/                      # common.js + one file per page
│   └── images/
│
└── templates/
    ├── base.html
    ├── index.html                # Home
    ├── register.html             # Create profile
    ├── dashboard.html
    ├── workout.html
    ├── nutrition.html
    ├── progress.html
    └── chat.html
```

---

## ⚙️ Setup Instructions

### 1. Clone / unzip the project
```bash
cd FitnessBuddy
```

### 2. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Open `.env` and set a `SECRET_KEY`. To use **real IBM Granite responses**,
also fill in the watsonx.ai fields (see next section). To just try the app
out first, leave `USE_MOCK_AI=auto` — it will automatically use the
built-in mock AI until credentials are provided.

### 5. Run the app
```bash
python app.py
```
The database (`database.db`) is created automatically on first run, with a
demo user and two weeks of sample progress data seeded in.

Visit **http://localhost:5000** in your browser.

---

## ☁️ IBM Cloud Lite / watsonx.ai Setup (for live Granite responses)

1. **Create an IBM Cloud account** (Lite/free tier is enough):
   https://cloud.ibm.com/registration

2. **Create a watsonx.ai Runtime (Machine Learning) service** on the Lite
   plan: https://cloud.ibm.com/catalog/services/watsonxai-runtime

3. **Create a watsonx.ai Project**:
   - Go to https://dataplatform.cloud.ibm.com
   - Create a new **Project**, associate it with the Machine Learning
     service instance you created above
   - Copy the **Project ID** from the project's *Manage* tab

4. **Generate an IBM Cloud IAM API key**:
   - https://cloud.ibm.com/iam/apikeys → *Create an IBM Cloud API key*
   - Copy the key (you only see it once)

5. **Fill in `.env`**:
   ```
   WATSONX_API_KEY=<your IAM API key>
   WATSONX_PROJECT_ID=<your watsonx.ai project id>
   WATSONX_URL=https://us-south.ml.cloud.ibm.com   # match your region
   GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2     # or another Granite model available to you
   USE_MOCK_AI=auto
   ```

6. Restart the app. `services/granite_service.py` will now exchange your
   API key for an IAM bearer token and call the Granite model on
   watsonx.ai for every AI feature (workouts, nutrition, motivation, chat).

> If the watsonx.ai call ever fails (network issue, quota, bad credentials),
> the app automatically and silently falls back to the rule-based mock AI so
> the user experience is never broken.

---

## 🧠 How the AI Layer Works (`services/granite_service.py`)

1. `_get_iam_token()` exchanges `WATSONX_API_KEY` for a short-lived bearer
   token via IBM Cloud IAM, caching it until it's close to expiry.
2. `call_granite(prompt, ...)` POSTs to the watsonx.ai
   `/ml/v1/text/generation` endpoint with your `GRANITE_MODEL_ID` and
   `WATSONX_PROJECT_ID`.
3. Task-specific helpers (`generate_workout_plan`, `generate_nutrition_plan`,
   `generate_motivation`, `chat_with_coach`, etc.) build a tailored prompt
   from the user's profile, call Granite, and return the generated text.
4. Each helper has a matching local mock generator used automatically when
   credentials are missing, `USE_MOCK_AI=true`, or the API call errors out.

---

## 🗄️ Database Schema (SQLite)

**users** — id, name, age, gender, height, weight, goal, activity_level, created_at
**progress** — id, user_id, weight, water_intake, workout_done, date
**chat_history** — id, user_id, question, response, timestamp

Re-create the database at any time:
```bash
python database/init_db.py
```

---

## 🔌 Key API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/register` | Create a user profile |
| GET/PUT | `/api/user/<id>` | Fetch / update a profile |
| POST | `/api/workout/plan` | AI 7-day workout plan |
| POST | `/api/workout/home` | AI quick home workout |
| GET | `/api/workout/tip` | AI fitness tip |
| POST | `/api/nutrition/plan` | AI meal plan + calorie target |
| GET | `/api/motivation` | AI motivational quote + habit tip |
| POST | `/api/progress` | Log today's weight/water/workout |
| GET | `/api/progress/<user_id>` | Progress history + weekly summary |
| POST | `/api/chat` | Chat with the AI coach |
| GET | `/api/chat/history/<user_id>` | Chat history |

All API responses are JSON in the shape `{ "success": true/false, ... }`,
with errors returned as `{ "success": false, "error": "..." }` and an
appropriate HTTP status code.

---

## 🚀 Deploying on IBM Cloud (optional)

The app is a standard Flask/WSGI app (`gunicorn` is included in
`requirements.txt`), so it can be deployed as:
- an **IBM Cloud Code Engine** application (`gunicorn app:app`), or
- an **IBM Cloud Foundry** app, or
- containerized and pushed to **IBM Cloud Container Registry**.

Set the same environment variables from `.env` in your IBM Cloud
service/app configuration instead of a local `.env` file.

---

## 🛡️ Error Handling

- Form/API inputs are validated (missing fields, non-numeric age/height/weight).
- All SQLite queries are parameterized to prevent SQL injection.
- `granite_service.py` catches network/auth/API errors and falls back to
  mock responses rather than crashing a request.
- Flask `404` and `500` handlers return sensible JSON/HTML fallbacks.

---

## 📄 License

This project is provided as a learning/demo template — feel free to adapt
it for coursework, portfolios, or your own fitness app.
