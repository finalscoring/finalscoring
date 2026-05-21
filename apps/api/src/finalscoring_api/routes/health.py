from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from finalscoring_api.dependencies import get_db

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    # Check the database connection
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception:
        db_status = "error"

    return {"status": "ok", "database": db_status}
