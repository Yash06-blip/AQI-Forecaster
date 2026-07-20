from pathlib import Path

# ======================================================
# PROJECT PATHS
# ======================================================

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATH = BASE_DIR / "models" / "delhi_aqi_model.pkl"

DATA_PATH = BASE_DIR / "data" / "processed" / "delhi_aqi_clean.csv"

TEMPLATES_DIR = BASE_DIR / "templates"

STATIC_DIR = BASE_DIR / "static"

# ======================================================
# APPLICATION
# ======================================================

APP_TITLE = "Delhi AQI Forecasting API"

APP_DESCRIPTION = (
    "Predicts Delhi AQI 24 hours ahead using historical pollution and weather data."
)

APP_VERSION = "1.0.0"