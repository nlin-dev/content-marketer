from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.routes.users import router as users_router
from app.routes.projects import router as projects_router
from app.routes.claims import router as claims_router
from app.routes.assets import router as assets_router
from app.routes.content import router as content_router
from app.routes.comments import router as comments_router
from app.routes.export import router as export_router

app = FastAPI(title="Content Marketer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-User-Id", "Authorization"],
)

app.include_router(users_router)
app.include_router(projects_router)
app.include_router(claims_router)
app.include_router(assets_router)
app.include_router(content_router)
app.include_router(comments_router)
app.include_router(export_router)

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/health")
async def health():
    return {"status": "ok"}
