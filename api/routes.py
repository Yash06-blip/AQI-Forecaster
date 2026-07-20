from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from api.schemas import ForecastRequest, ForecastResponse
from api.predictor import predict, get_model_info, get_history

router = APIRouter()

templates = Jinja2Templates(directory="templates")


# ======================================================
# HOME
# ======================================================

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"request": request}
    )


# ======================================================
# HEALTH
# ======================================================

@router.get("/health")
def health_check():
    return get_model_info()


# ======================================================
# FORECAST
# ======================================================

@router.post("/forecast", response_model=ForecastResponse)
def forecast(request: ForecastRequest):
    try:
        return predict(request)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


# ======================================================
# HISTORY
# ======================================================

@router.get("/history")
def history(days: int = 30):
    try:
        return get_history(days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))