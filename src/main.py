from fastapi import FastAPI

from src.routers import router


app = FastAPI(
    title="Organizations API",
    description="API для управления организациями, зданиями и видами деятельности",
    version="1.0.0"
)


app.include_router(router)
