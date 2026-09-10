-- Fitness Buddy database schema (SQLite)

CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    age             INTEGER NOT NULL,
    gender          TEXT NOT NULL,
    height          REAL NOT NULL,        -- cm
    weight          REAL NOT NULL,        -- kg
    goal            TEXT NOT NULL,        -- weight_loss | muscle_gain | maintenance | endurance
    activity_level  TEXT NOT NULL,        -- sedentary | light | moderate | active | very_active
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS progress (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    weight          REAL,
    water_intake    REAL,                 -- liters
    workout_done    INTEGER DEFAULT 0,    -- 0/1 boolean
    date            TEXT NOT NULL,        -- YYYY-MM-DD
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chat_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    question        TEXT NOT NULL,
    response        TEXT NOT NULL,
    timestamp       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_progress_user ON progress (user_id, date);
CREATE INDEX IF NOT EXISTS idx_chat_user ON chat_history (user_id, timestamp);
