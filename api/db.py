import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./ggpt.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False, "timeout": 30},
)

if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA busy_timeout=30000")
        try:
            cur.execute("PRAGMA journal_mode=WAL")
        except Exception:
            pass
        try:
            cur.execute("PRAGMA synchronous=NORMAL")
        except Exception:
            pass
        cur.close()

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
    _add_columns_if_missing()


def _add_columns_if_missing():
    """Idempotent ALTER TABLE for new columns added after the table was first
    created. SQLite's `create_all` only creates missing tables, not missing
    columns — so a fresh schema picks new columns up automatically, but an
    existing DB needs a one-time ALTER on upgrade.
    """
    from sqlalchemy import inspect, text
    insp = inspect(engine)
    additions = {
        "runs": [
            ("current_stage", "VARCHAR"),
        ],
    }
    for table, cols in additions.items():
        if table not in insp.get_table_names():
            continue
        existing = {c["name"] for c in insp.get_columns(table)}
        for name, sqltype in cols:
            if name in existing:
                continue
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sqltype}"))


def reset_db():
    """Drop every table and recreate the fresh 2-table schema. Destroys data."""
    from api import models  # noqa: F401
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
