import joblib
import pandas as pd
from api.logger import logger
from api.config import MODEL_PATH, DATA_PATH
from api.schemas import ForecastRequest, ForecastResponse
from api.utils import get_aqi_category
from fastapi import HTTPException


# ======================================================
# LOAD MODEL
# ======================================================

artifact = joblib.load(MODEL_PATH)

model = artifact["model"]
FEATURES = artifact["features"]

logger.info("Model loaded successfully.")
logger.info(f"Features: {len(FEATURES)}")
logger.info(f"Trained up to: {artifact['trained_on']}")
logger.info(f"Backtest MAE: {artifact['backtest_MAE_2018plus']}")


# ======================================================
# HEALTH INFO
# ======================================================

def get_model_info():
    return {
        "status": "healthy",
        "model_version": "1.0.0",
        "trained_up_to": artifact["trained_on"],
        "backtest_MAE": artifact["backtest_MAE_2018plus"],
        "backtest_MAPE_percent": artifact["backtest_MAPE_2018plus"],
        "n_features": len(FEATURES),
    }


# ======================================================
# PREDICTION
# ======================================================

def predict(request: ForecastRequest) -> ForecastResponse:
    logger.info("Forecast prediction requested.")

    try:
        dt = pd.to_datetime(request.forecast_datetime)

        feature_dict = {
            "hour": dt.hour,
            "day_of_week": dt.dayofweek,
            "month": dt.month,
            "is_weekend": int(dt.dayofweek >= 5),
            "season": {
                12: 0, 1: 0, 2: 0,
                3: 1, 4: 1, 5: 1,
                6: 2, 7: 2, 8: 2,
                9: 3, 10: 3, 11: 3
            }[dt.month],

            "AQI_lag_24h": request.AQI_lag_24h,
            "AQI_lag_48h": request.AQI_lag_48h,
            "AQI_lag_72h": request.AQI_lag_72h,
            "AQI_lag_168h": request.AQI_lag_168h,
            "AQI_lag_8760h": request.AQI_lag_8760h,

            "AQI_rolling_mean_24h": request.AQI_rolling_mean_24h,
            "AQI_rolling_mean_48h": request.AQI_rolling_mean_48h,
            "AQI_rolling_std_24h": request.AQI_rolling_std_24h,
            "AQI_rolling_max_24h": request.AQI_rolling_max_24h,
            "AQI_rolling_min_24h": request.AQI_rolling_min_24h,

            "PM2.5": request.PM2_5,
            "PM10": request.PM10,
            "NO2": request.NO2,
            "CO": request.CO,
            "SO2": request.SO2,
            "O3": request.O3,

            "temperature_lag_24h": request.temperature_lag_24h,
            "humidity_lag_24h": request.humidity_lag_24h,
            "windspeed_lag_24h": request.windspeed_lag_24h,
            "precipitation_lag_24h": request.precipitation_lag_24h,

            "temperature_rolling_mean_24h": request.temperature_rolling_mean_24h,
            "humidity_rolling_mean_24h": request.humidity_rolling_mean_24h,
            "windspeed_rolling_mean_24h": request.windspeed_rolling_mean_24h,
            "precipitation_rolling_mean_24h": request.precipitation_rolling_mean_24h,
        }

        input_df = pd.DataFrame([feature_dict])[FEATURES]

        predicted_aqi = float(model.predict(input_df)[0])
        predicted_aqi = max(0, min(500, predicted_aqi))

        mae = artifact["backtest_MAE_2018plus"]

        lower = max(0, predicted_aqi - mae)
        upper = min(500, predicted_aqi + mae)

        return ForecastResponse(
            forecast_datetime=str(dt + pd.Timedelta(hours=24)),
            predicted_AQI=round(predicted_aqi, 1),
            AQI_lower_bound=round(lower, 1),
            AQI_upper_bound=round(upper, 1),
            AQI_category=get_aqi_category(predicted_aqi),
            model_MAE=artifact["backtest_MAE_2018plus"],
            model_MAPE_percent=artifact["backtest_MAPE_2018plus"],
            message=(
                f"Predicted AQI for Delhi 24 hours from "
                f"{dt.strftime('%Y-%m-%d %H:%M')} "
                f"is {round(predicted_aqi,1)} "
                f"({get_aqi_category(predicted_aqi)})"
            ),
        )

    except Exception:
        logger.exception("Prediction failed.")

        raise HTTPException(
            status_code=500,
            detail="Unable to generate AQI prediction."
        )


# ======================================================
# HISTORY
# ======================================================

def get_history(days: int = 30):
    logger.info(f"History requested for last {days} days.")

    try:
        df = pd.read_csv(DATA_PATH)

        df["Datetime"] = pd.to_datetime(df["Datetime"])

        df = df.sort_values("Datetime")

        df["date"] = df["Datetime"].dt.date

        daily = df.groupby("date")["AQI"].mean().reset_index()

        daily = daily.tail(days)

        return {
            "dates": [str(d) for d in daily["date"]],
            "aqi_values": [round(v, 1) for v in daily["AQI"]],
            "source": "CPCB Delhi monitoring data 2015-2020",
            "days": len(daily),
        }

    except Exception:
        logger.exception("Failed to retrieve historical AQI data.")

        raise HTTPException(
            status_code=500,
            detail="Unable to retrieve historical AQI data."
        )