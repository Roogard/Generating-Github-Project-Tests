import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from api.db import init_db
from api.routes import router, analytics_router
from src.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()
    yield


app = FastAPI(title="GGPT API", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(router)
app.include_router(analytics_router)

# Serve React build in production
_dist = os.path.join(os.path.dirname(__file__), "..", "webapp", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="static")


def start():
    """Entrypoint for `ggpt-api` CLI command."""
    import uvicorn
    uvicorn.run(
        "api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["api"],
    )
