from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
import numpy as np
import joblib
from datetime import datetime
import os

# ── LOAD MODEL ────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), '..', 'models', 'delhi_aqi_model.pkl')

artifact = joblib.load(MODEL_PATH)
model    = artifact['model']
FEATURES = artifact['features']

print(f"Model loaded. Features: {len(FEATURES)}")
print(f"Trained on data up to: {artifact['trained_on']}")
print(f"Backtest MAE (2018+): {artifact['backtest_MAE_2018plus']}")

# ── APP ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Delhi AQI Forecasting API",
    description="Predicts Delhi AQI 24 hours ahead using historical pollution and weather data.",
    version="1.0.0"
)

# ── REQUEST SCHEMA ────────────────────────────────────────────────
class ForecastRequest(BaseModel):
    # AQI lag inputs
    AQI_lag_24h:  float = Field(..., description="AQI 24 hours ago", ge=0, le=500)
    AQI_lag_48h:  float = Field(..., description="AQI 48 hours ago", ge=0, le=500)
    AQI_lag_72h:  float = Field(..., description="AQI 72 hours ago", ge=0, le=500)
    AQI_lag_168h: float = Field(..., description="AQI 168 hours ago (1 week)", ge=0, le=500)
    AQI_lag_8760h: float = Field(..., description="AQI 8760 hours ago (1 year)", ge=0, le=500)

    # Rolling AQI stats
    AQI_rolling_mean_24h: float = Field(..., description="Mean AQI over last 24h", ge=0, le=500)
    AQI_rolling_mean_48h: float = Field(..., description="Mean AQI over last 48h", ge=0, le=500)
    AQI_rolling_std_24h:  float = Field(..., description="Std dev of AQI over last 24h", ge=0)
    AQI_rolling_max_24h:  float = Field(..., description="Max AQI over last 24h", ge=0, le=500)
    AQI_rolling_min_24h:  float = Field(..., description="Min AQI over last 24h", ge=0, le=500)

    # Pollutants
    PM2_5: float = Field(..., alias="PM2.5", description="PM2.5 reading", ge=0)
    PM10:  float = Field(..., description="PM10 reading", ge=0)
    NO2:   float = Field(..., description="NO2 reading", ge=0)
    CO:    float = Field(..., description="CO reading", ge=0)
    SO2:   float = Field(..., description="SO2 reading", ge=0)
    O3:    float = Field(..., description="O3 reading", ge=0)

    # Weather
    temperature_lag_24h:          float = Field(..., description="Temperature 24h ago (°C)")
    humidity_lag_24h:             float = Field(..., description="Humidity 24h ago (%)", ge=0, le=100)
    windspeed_lag_24h:            float = Field(..., description="Wind speed 24h ago (km/h)", ge=0)
    precipitation_lag_24h:        float = Field(..., description="Precipitation 24h ago (mm)", ge=0)
    temperature_rolling_mean_24h: float = Field(..., description="Mean temperature over last 24h (°C)")
    humidity_rolling_mean_24h:    float = Field(..., description="Mean humidity over last 24h (%)", ge=0, le=100)
    windspeed_rolling_mean_24h:   float = Field(..., description="Mean wind speed over last 24h (km/h)", ge=0)
    precipitation_rolling_mean_24h: float = Field(..., description="Mean precipitation over last 24h (mm)", ge=0)

    # Temporal — auto computed from datetime if not provided
    forecast_datetime: str = Field(
        default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="Datetime for which to generate forecast (YYYY-MM-DD HH:MM:SS)"
    )

    class Config:
        allow_population_by_field_name = True

# ── RESPONSE SCHEMA ───────────────────────────────────────────────
class ForecastResponse(BaseModel):
    forecast_datetime:     str
    predicted_AQI:         float
    AQI_lower_bound:       float
    AQI_upper_bound:       float
    AQI_category:          str
    model_MAE:             float
    model_MAPE_percent:    float
    message:               str

# ── HELPER: AQI CATEGORY ──────────────────────────────────────────
def get_aqi_category(aqi: float) -> str:
    if aqi <= 50:   return "Good"
    if aqi <= 100:  return "Satisfactory"
    if aqi <= 200:  return "Moderate"
    if aqi <= 300:  return "Poor"
    if aqi <= 400:  return "Very Poor"
    return "Severe"

# ── ROUTES ────────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "model_version": "1.0.0",
        "trained_up_to": artifact['trained_on'],
        "backtest_MAE": artifact['backtest_MAE_2018plus'],
        "backtest_MAPE_percent": artifact['backtest_MAPE_2018plus'],
        "n_features": len(FEATURES)
    }

@app.post("/forecast", response_model=ForecastResponse)
def forecast(request: ForecastRequest):
    try:
        # Parse forecast datetime for temporal features
        dt = pd.to_datetime(request.forecast_datetime)

        # Build feature dict matching training feature names exactly
        feature_dict = {
            'hour':        dt.hour,
            'day_of_week': dt.dayofweek,
            'month':       dt.month,
            'is_weekend':  int(dt.dayofweek >= 5),
            'season':      {12:0,1:0,2:0,3:1,4:1,5:1,
                           6:2,7:2,8:2,9:3,10:3,11:3}[dt.month],
            'AQI_lag_24h':  request.AQI_lag_24h,
            'AQI_lag_48h':  request.AQI_lag_48h,
            'AQI_lag_72h':  request.AQI_lag_72h,
            'AQI_lag_168h': request.AQI_lag_168h,
            'AQI_lag_8760h': request.AQI_lag_8760h,
            'AQI_rolling_mean_24h': request.AQI_rolling_mean_24h,
            'AQI_rolling_mean_48h': request.AQI_rolling_mean_48h,
            'AQI_rolling_std_24h':  request.AQI_rolling_std_24h,
            'AQI_rolling_max_24h':  request.AQI_rolling_max_24h,
            'AQI_rolling_min_24h':  request.AQI_rolling_min_24h,
            'PM2.5': request.PM2_5,
            'PM10':  request.PM10,
            'NO2':   request.NO2,
            'CO':    request.CO,
            'SO2':   request.SO2,
            'O3':    request.O3,
            'temperature_lag_24h':           request.temperature_lag_24h,
            'humidity_lag_24h':              request.humidity_lag_24h,
            'windspeed_lag_24h':             request.windspeed_lag_24h,
            'precipitation_lag_24h':         request.precipitation_lag_24h,
            'temperature_rolling_mean_24h':  request.temperature_rolling_mean_24h,
            'humidity_rolling_mean_24h':     request.humidity_rolling_mean_24h,
            'windspeed_rolling_mean_24h':    request.windspeed_rolling_mean_24h,
            'precipitation_rolling_mean_24h': request.precipitation_rolling_mean_24h,
        }

        # Convert to DataFrame — model expects a DataFrame not a dict
        input_df = pd.DataFrame([feature_dict])[FEATURES]

        # Predict
        predicted_aqi = float(model.predict(input_df)[0])
        predicted_aqi = max(0, min(500, predicted_aqi))  # Clamp to valid AQI range

        # Confidence range based on backtest MAE
        mae = artifact['backtest_MAE_2018plus']
        lower = max(0,   predicted_aqi - mae)
        upper = min(500, predicted_aqi + mae)

        return ForecastResponse(
            forecast_datetime=str(dt + pd.Timedelta(hours=24)),
            predicted_AQI=round(predicted_aqi, 1),
            AQI_lower_bound=round(lower, 1),
            AQI_upper_bound=round(upper, 1),
            AQI_category=get_aqi_category(predicted_aqi),
            model_MAE=artifact['backtest_MAE_2018plus'],
            model_MAPE_percent=artifact['backtest_MAPE_2018plus'],
            message=f"Predicted AQI for Delhi 24 hours from {dt.strftime('%Y-%m-%d %H:%M')} "
                    f"is {round(predicted_aqi, 1)} ({get_aqi_category(predicted_aqi)})"
        )

    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))
