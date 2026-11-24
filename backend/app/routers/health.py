from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.Base import MyDb
from app.scheme.health import HealthResponse

router = APIRouter(tags=["Health"], prefix="/health")


@router.get("/live", response_model=HealthResponse)
async def live():
    return {"status": "ok"}


@router.get(
    "/ready",
    response_model=HealthResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Database unavailable"}},
)
async def ready(db: MyDb):
    try:
        await db.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError) as e:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Database unavailable") from e
    return {"status": "ok"}
