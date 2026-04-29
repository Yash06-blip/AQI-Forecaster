# AQI Forecaster

A production-grade machine learning API that forecasts Delhi's Air Quality Index (AQI) **24 hours ahead** using historical pollution data and weather signals.

Built with Python, scikit-learn, and FastAPI. Deployed publicly on Render.

---

## Problem

Delhi's AQI swings dramatically — from 50 to 450 within days during winter. 
Government portals show current readings but offer no forecast. This API closes 
that gap by predicting what the AQI will be 24 hours from now, giving residents 
and applications actionable advance warning.

---

## Results

| Model | MAE | MAPE | RMSE |
|---|---|---|---|
| Linear Regression ✅ | 39.3 | 21.0% | 57.1 |
| LightGBM | 41.6 | 22.4% | 61.4 |
| Random Forest | 42.7 | 23.4% | 64.6 |

Evaluated via **rolling backtest across 42 windows (2018–2020)** — never trained on future data.

Linear Regression outperformed tree-based models, indicating the engineered features 
have a predominantly linear relationship with 24-hour AQI — complexity added noise, not signal.

---

## Architecture
Raw Data (Kaggle CPCB + Open-Meteo Weather)
↓
Data Cleaning (forward-fill, hourly median imputation)
↓
Feature Engineering (29 features: lag, rolling stats, temporal, weather)
↓
Model Training + Rolling Backtest Evaluation
↓
Serialized Model (joblib)
↓
FastAPI Service → POST /forecast → JSON prediction + confidence range

---

## Features Used (29 total)

**Temporal:** hour, day_of_week, month, is_weekend, season

**AQI Lags:** 24h, 48h, 72h, 168h (1 week), 8760h (1 year)

**Rolling Statistics:** 24h mean, 48h mean, 24h std, 24h max, 24h min

**Pollutants:** PM2.5, PM10, NO2, CO, SO2, O3

**Weather (lagged 24h):** temperature, humidity, wind speed, precipitation + 24h rolling means

---

## API Endpoints

### `GET /health`
Returns model status, version, and backtest metrics.

```json
{
  "status": "healthy",
  "model_version": "1.0.0",
  "trained_up_to": "2020-06-30",
  "backtest_MAE": 39.3,
  "backtest_MAPE_percent": 21,
  "n_features": 29
}
```

### `POST /forecast`
Returns 24-hour AQI prediction with confidence range and category.

**Sample request:**
```json
{
  "AQI_lag_24h": 187.0,
  "AQI_lag_48h": 210.0,
  "AQI_lag_72h": 198.0,
  "AQI_lag_168h": 175.0,
  "AQI_lag_8760h": 220.0,
  "AQI_rolling_mean_24h": 195.0,
  "AQI_rolling_mean_48h": 200.0,
  "AQI_rolling_std_24h": 18.5,
  "AQI_rolling_max_24h": 230.0,
  "AQI_rolling_min_24h": 160.0,
  "PM2.5": 98.5,
  "PM10": 145.0,
  "NO2": 52.3,
  "CO": 1.8,
  "SO2": 14.2,
  "O3": 28.5,
  "temperature_lag_24h": 18.5,
  "humidity_lag_24h": 72.0,
  "windspeed_lag_24h": 8.2,
  "precipitation_lag_24h": 0.0,
  "temperature_rolling_mean_24h": 19.2,
  "humidity_rolling_mean_24h": 68.0,
  "windspeed_rolling_mean_24h": 9.1,
  "precipitation_rolling_mean_24h": 0.0,
  "forecast_datetime": "2019-11-15 14:00:00"
}
```

**Sample response:**
```json
{
  "forecast_datetime": "2019-11-16 14:00:00",
  "predicted_AQI": 233.2,
  "AQI_lower_bound": 193.9,
  "AQI_upper_bound": 272.5,
  "AQI_category": "Poor",
  "model_MAE": 39.3,
  "model_MAPE_percent": 21,
  "message": "Predicted AQI for Delhi 24 hours from 2019-11-15 14:00 is 233.2 (Poor)"
}
```

---

## Local Setup

```bash
# Clone the repo
git clone https://github.com/Yash06-blip/AQI-Forecaster.git
cd AQI-Forecaster

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn api.main:app --reload
```

Then open `http://127.0.0.1:8000/docs` for the interactive API documentation.

---

## Data Sources

| Source | What it provides |
|---|---|
| [Kaggle — Air Quality Data in India](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india) | Hourly AQI + pollutant readings for Delhi, 2015–2020 |
| [Open-Meteo](https://open-meteo.com) | Free historical hourly weather data — temperature, humidity, wind, precipitation |

---

## Project Structure
AQI-Forecaster/
│
├── api/
│   └── main.py           ← FastAPI application
│
├── notebooks/
│   ├── 01_exploration.ipynb     ← Data cleaning + feature engineering
│   └── 02_model_training.ipynb  ← Model training + backtest evaluation
│
├── src/                  ← (pipeline modules — v2 roadmap)
│
├── requirements.txt
├── Dockerfile
└── README.md

---

## Key Engineering Decisions

**Why Linear Regression over LightGBM?**
After tuning LightGBM across 5 parameter sets, Linear Regression consistently 
outperformed it on the holdout set. The engineered lag and rolling features 
create a near-linear relationship with the target — LightGBM's additional 
complexity overfit noise rather than learning signal.

**Why rolling backtest instead of random split?**
AQI data has strong temporal dependency. A random split would allow the model 
to train on 2019 data to predict 2017 — that's data leakage. The rolling 
backtest strictly trains on the past to predict the next unseen month, 
accurately simulating real-world deployment.

**Why 24-hour forecast horizon?**
Initial 1-hour forecasting showed R²=0.995 with AQI_lag_1h alone — the model 
was just copying the previous hour. Switching to 24-hour forecasting forced 
the model to learn genuine temporal and meteorological patterns.

---

## Live API

🔗 🔗 **Live API:** https://aqi-forecaster-q1vv.onrender.com/docs

--- 

*Built by Yash Bagde*
