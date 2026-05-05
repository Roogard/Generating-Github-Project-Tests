import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Two SQLite files:
#   ggpt.db          — the main runner DB. Writable. Lives in the working
#                      dir, gitignored. Where src/persist.py + src/runner.py
#                      record new runs.
#   data/featured.db — the small, committed DB that backs the website's
#                      Database tab. Read-only at runtime; rebuilt by
#                      scripts/build_featured_db.py.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./ggpt.db")
FEATURED_DB_PATH = os.environ.get(
    "FEATURED_DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "featured.db"),
)
FEATURED_DATABASE_URL = "sqlite:///" + os.path.abspath(FEATURED_DB_PATH).replace("\\", "/")


def _make_engine(url):
    eng = create_engine(url, connect_args={"check_same_thread": False, "timeout": 30})
    if url.startswith("sqlite"):
        @event.listens_for(eng, "connect")
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
    return eng


engine = _make_engine(DATABASE_URL)
featured_engine = _make_engine(FEATURED_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
FeaturedSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=featured_engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_featured_db():
    db = FeaturedSessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from api import models  # noqa: F401 — register ORM classes
    Base.metadata.create_all(bind=engine)
    if os.path.isfile(os.path.abspath(FEATURED_DB_PATH)):
        # Don't auto-create the featured DB — only do schema upgrades on it.
        # It's built explicitly by scripts/build_featured_db.py.
        Base.metadata.create_all(bind=featured_engine)
    _add_columns_if_missing(engine)
    if os.path.isfile(os.path.abspath(FEATURED_DB_PATH)):
        _add_columns_if_missing(featured_engine)


def _add_columns_if_missing(target_engine):
    """Idempotent ALTER TABLE for new columns added after the table was first
    created. SQLite's `create_all` only creates missing tables, not missing
    columns — so a fresh schema picks new columns up automatically, but an
    existing DB needs a one-time ALTER on upgrade.
    """
    from sqlalchemy import inspect, text
    insp = inspect(target_engine)
    additions = {
        "runs": [
            ("current_stage", "VARCHAR"),
            ("problem_statement", "TEXT"),
        ],
    }
    for table, cols in additions.items():
        if table not in insp.get_table_names():
            continue
        existing = {c["name"] for c in insp.get_columns(table)}
        for name, sqltype in cols:
            if name in existing:
                continue
            with target_engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {sqltype}"))


def reset_db():
    """Drop every table and recreate the fresh 2-table schema. Destroys data."""
    from api import models  # noqa: F401
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def reset_featured_db():
    """Drop and recreate the featured DB schema. Used by the build script."""
    from api import models  # noqa: F401
    os.makedirs(os.path.dirname(os.path.abspath(FEATURED_DB_PATH)), exist_ok=True)
    Base.metadata.drop_all(bind=featured_engine)
    Base.metadata.create_all(bind=featured_engine)
