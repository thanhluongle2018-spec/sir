from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import channels, datasources, items, meta, tasks
from app.config import get_settings
from app.db import init_db
from app.platforms.http_util import close_http_client
from app.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("jp-monitor")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Path("/workspace/data").mkdir(parents=True, exist_ok=True)
    init_db()
    start_scheduler()
    logger.info("application started")
    yield
    stop_scheduler()
    await close_http_client()
    logger.info("application stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list + ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(tasks.router)
    app.include_router(items.router)
    app.include_router(channels.router)
    app.include_router(meta.router)
    app.include_router(datasources.router)

    static_dir = Path(settings.static_dir)
    if static_dir.exists():
        assets = static_dir / "assets"
        if assets.exists():
            app.mount("/assets", StaticFiles(directory=str(assets)), name="assets")

        @app.get("/")
        async def index_page():
            index = static_dir / "index.html"
            if index.exists():
                return FileResponse(index)
            return {"detail": "frontend not built", "hint": "cd frontend && npm run build"}

        @app.get("/{full_path:path}")
        async def spa_fallback(full_path: str):
            if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi"):
                return {"detail": "Not Found"}
            # Prefer exact static file if present
            candidate = static_dir / full_path
            if candidate.is_file():
                return FileResponse(candidate)
            index = static_dir / "index.html"
            if index.exists():
                return FileResponse(index)
            return {"detail": "frontend not built"}

    return app


app = create_app()
