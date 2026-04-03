from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from quant_cover_api.api.dependencies import get_db


router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck(session: Session = Depends(get_db)) -> dict[str, str]:
    session.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "service": "quant-cover-api",
        "database": "ok",
    }
