import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./ghtest.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_columns():
    """Add columns that exist in the ORM but may be absent in older DB files."""
    with engine.connect() as conn:
        gt_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(generated_tests)"))}
        if "coverage_pct" not in gt_cols:
            conn.execute(text("ALTER TABLE generated_tests ADD COLUMN coverage_pct REAL"))
            conn.commit()
        run_cols = {row[1] for row in conn.execute(text("PRAGMA table_info(runs)"))}
        if "progress_current" not in run_cols:
            conn.execute(text("ALTER TABLE runs ADD COLUMN progress_current INTEGER DEFAULT 0"))
            conn.commit()
        if "progress_total" not in run_cols:
            conn.execute(text("ALTER TABLE runs ADD COLUMN progress_total INTEGER DEFAULT 0"))
            conn.commit()


def init_db():
    from api import models  # noqa: F401 — import so models are registered
    Base.metadata.create_all(bind=engine)
    _ensure_columns()
