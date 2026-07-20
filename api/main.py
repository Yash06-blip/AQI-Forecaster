from api.config import (
    APP_TITLE,
    APP_DESCRIPTION,
    APP_VERSION,
    STATIC_DIR,
    TEMPLATES_DIR,
)
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routes import router

app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
)

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)

app.include_router(router)