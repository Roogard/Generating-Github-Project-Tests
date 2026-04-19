import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.db import init_db
from api.routes import router
from api.db_routes import router as db_router
from api.vectordb_routes import router as vectordb_router
from api.analytics_routes import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="GHTest API", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

app.include_router(router)
app.include_router(db_router)
app.include_router(vectordb_router)
app.include_router(analytics_router)

# Serve React build in production
_dist = os.path.join(os.path.dirname(__file__), "..", "webapp", "dist")
if os.path.isdir(_dist):
    app.mount("/", StaticFiles(directory=_dist, html=True), name="static")


def start():
    """Entrypoint for `ghtest-api` CLI command."""
    import uvicorn
    uvicorn.run(
        "api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=["api"],
    )
