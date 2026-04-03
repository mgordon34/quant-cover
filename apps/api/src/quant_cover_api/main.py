from fastapi import FastAPI

from quant_cover_api.api.health import router as health_router
from quant_cover_api.api.strategies import router as strategies_router
from quant_cover_api.api.users import router as users_router
from quant_cover_api.config import get_settings


settings = get_settings()

app = FastAPI(title="Quant Cover API", version="0.1.0")
app.include_router(health_router)
app.include_router(strategies_router)
app.include_router(users_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "message": "hello world",
        "service": "quant-cover-api",
        "environment": settings.app_env,
    }
