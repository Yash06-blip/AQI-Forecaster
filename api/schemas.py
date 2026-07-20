from pydantic import BaseModel, Field
from datetime import datetime


# ── REQUEST SCHEMA ────────────────────────────────────────────────
class ForecastRequest(BaseModel):
    AQI_lag_24h:  float = Field(..., description="AQI 24 hours ago", ge=0, le=500)
    AQI_lag_48h:  float = Field(..., description="AQI 48 hours ago", ge=0, le=500)
    AQI_lag_72h:  float = Field(..., description="AQI 72 hours ago", ge=0, le=500)
    AQI_lag_168h: float = Field(..., description="AQI 168 hours ago (1 week)", ge=0, le=500)
    AQI_lag_8760h: float = Field(..., description="AQI 8760 hours ago (1 year)", ge=0, le=500)
    AQI_rolling_mean_24h: float = Field(..., description="Mean AQI over last 24h", ge=0, le=500)
    AQI_rolling_mean_48h: float = Field(..., description="Mean AQI over last 48h", ge=0, le=500)
    AQI_rolling_std_24h:  float = Field(..., description="Std dev of AQI over last 24h", ge=0)
    AQI_rolling_max_24h:  float = Field(..., description="Max AQI over last 24h", ge=0, le=500)
    AQI_rolling_min_24h:  float = Field(..., description="Min AQI over last 24h", ge=0, le=500)
    PM2_5: float = Field(..., alias="PM2.5", description="PM2.5 reading", ge=0)
    PM10:  float = Field(..., description="PM10 reading", ge=0)
    NO2:   float = Field(..., description="NO2 reading", ge=0)
    CO:    float = Field(..., description="CO reading", ge=0)
    SO2:   float = Field(..., description="SO2 reading", ge=0)
    O3:    float = Field(..., description="O3 reading", ge=0)
    temperature_lag_24h:          float = Field(..., description="Temperature 24h ago (°C)")
    humidity_lag_24h:             float = Field(..., description="Humidity 24h ago (%)", ge=0, le=100)
    windspeed_lag_24h:            float = Field(..., description="Wind speed 24h ago (km/h)", ge=0)
    precipitation_lag_24h:        float = Field(..., description="Precipitation 24h ago (mm)", ge=0)
    temperature_rolling_mean_24h: float = Field(..., description="Mean temperature over last 24h (°C)")
    humidity_rolling_mean_24h:    float = Field(..., description="Mean humidity over last 24h (%)", ge=0, le=100)
    windspeed_rolling_mean_24h:   float = Field(..., description="Mean wind speed over last 24h (km/h)", ge=0)
    precipitation_rolling_mean_24h: float = Field(..., description="Mean precipitation over last 24h (mm)", ge=0)
    forecast_datetime: str = Field(
        default=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        description="Datetime for which to generate forecast (YYYY-MM-DD HH:MM:SS)"
    )

    model_config = {"populate_by_name": True}

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