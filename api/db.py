import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./ggpt.db")

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


def init_db():
    from api import models  # noqa: F401 — register ORM classes
    Base.metadata.create_all(bind=engine)


def reset_db():
    """Drop every table and recreate the fresh 2-table schema. Destroys data."""
    from api import models  # noqa: F401
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
