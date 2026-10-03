"""Agregator seluruh sub-routers API KeyQuiz."""
from fastapi import APIRouter
from app.api.routes_essay import router as essay_router
from app.api.routes_scan import router as scan_router
from app.api.routes_quiz import router as quiz_router
from app.api.routes_auth import router as auth_router

api_router = APIRouter(prefix="/api")

api_router.include_router(essay_router)
api_router.include_router(scan_router)
api_router.include_router(quiz_router)
api_router.include_router(auth_router)
