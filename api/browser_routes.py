"""Read-only analytics summary (`/api/analytics/*`)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api import store
from api.db import get_db


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return store.summary_stats(db)
