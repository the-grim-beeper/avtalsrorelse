from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings

app = FastAPI(title="Avtalsrörelsen Simulator")

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.up\.railway\.app",
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import router

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok"}


# Serve frontend static files in production
# The build script copies frontend/dist/ to backend/static/
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    # Mount /assets first so static files are served directly
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    # Catch-all: serve index.html for SPA routing (must be last)
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = static_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(static_dir / "index.html")
