"""FastAPI application entry point."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.database import init_db
from app.routes import admin, public

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="ResumAI - Interactive Professional Profile")

# Signed session cookie used to track the visitor's registration across
# requests (welcome -> profile -> chat) without needing a login system.
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(public.router)
app.include_router(admin.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
