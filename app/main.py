# app/main.py

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.services.data_repository import DataRepository
from app.routers import auth, dashboard, campus, upload, academic, ixl, clima_disciplina, audit, comparativa, preescolar

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicializar la base de datos SQLite y sembrar usuarios por defecto al arrancar
    repo = DataRepository(db_path=settings.DB_PATH)
    print(f"[{settings.APP_NAME}] Base de datos inicializada en '{settings.DB_PATH}' con soporte Bcrypt.")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Dashboard Ejecutivo Académico para Instituto Agustín (FastAPI + Jinja2 + HTMX)",
    version="2.0.0",
    lifespan=lifespan
)

# Montar archivos estáticos
os.makedirs("app/static/css", exist_ok=True)
os.makedirs("app/static/js", exist_ok=True)
os.makedirs("app/static/img", exist_ok=True)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Incluir routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(campus.router)
app.include_router(upload.router)
app.include_router(academic.router)
app.include_router(ixl.router)
app.include_router(clima_disciplina.router)
app.include_router(audit.router)
app.include_router(comparativa.router)
app.include_router(preescolar.router)

@app.get("/")
async def root():
    return RedirectResponse(url="/dashboard", status_code=303)
