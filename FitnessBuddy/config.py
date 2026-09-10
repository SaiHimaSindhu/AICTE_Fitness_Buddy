"""
config.py
Central configuration for Fitness Buddy.

All secrets are read from environment variables so nothing sensitive
is ever hard-coded into source control. Create a `.env` file (see
README.md) or export these variables in your shell / IBM Cloud
runtime environment before starting the app.
"""

import os
from datetime import timedelta

# Load a local .env file if python-dotenv is installed (optional, dev convenience)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class Config:
    # ---------------------------------------------------------------
    # Flask core
    # ---------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "fitness-buddy-dev-secret-change-me")
    DEBUG = os.environ.get("FLASK_DEBUG", "True") == "True"
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # ---------------------------------------------------------------
    # SQLite database
    # ---------------------------------------------------------------
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, "database.db")

    # ---------------------------------------------------------------
    # IBM Cloud / watsonx.ai credentials
    #
    # Get these from IBM Cloud Lite:
    #   1. Create a "watsonx.ai Runtime" (Machine Learning) Lite service
    #   2. Create a project in watsonx.ai and note the Project ID
    #   3. Generate an IBM Cloud IAM API key from
    #      https://cloud.ibm.com/iam/apikeys
    # ---------------------------------------------------------------
    WATSONX_API_KEY = os.environ.get("WATSONX_API_KEY", "")
    WATSONX_PROJECT_ID = os.environ.get("WATSONX_PROJECT_ID", "")
    WATSONX_URL = os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
    WATSONX_IAM_URL = os.environ.get(
        "WATSONX_IAM_URL", "https://iam.cloud.ibm.com/identity/token"
    )
    # IBM Granite model served through watsonx.ai
    GRANITE_MODEL_ID = os.environ.get("GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2")
    WATSONX_VERSION = os.environ.get("WATSONX_VERSION", "2023-05-29")

    # If True, Granite calls are simulated with rule-based responses.
    # This lets the whole app run end-to-end even with no IBM Cloud
    # account configured yet (useful for local dev / grading / demos).
    USE_MOCK_AI = os.environ.get("USE_MOCK_AI", "auto")
