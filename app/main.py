import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from app.db.database import connect, disconnect

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    yield
    await disconnect()

app = FastAPI(
    title="Virtual World API",
    description="Симулятор виртуального мира с AI-агентами",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.controllers.system_controller import router as system_router
from app.controllers.text_controller import router as text_router
from app.controllers.action_controller import router as action_router
from app.controllers.logger_controller import router as logger_router

app.include_router(system_router, prefix="/api/v1")
app.include_router(text_router, prefix="/api/v1")
app.include_router(action_router, prefix="/api/v1")
app.include_router(logger_router, prefix="/api/v1")

STATIC_DIR = os.path.join(os.path.dirname(__file__), '../frontend/dist')
if os.path.exists(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=f"{STATIC_DIR}/assets"), name="assets")

@app.get("/")
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"service": "Virtual World API", "version": "2.0.0"}

@app.get("/{path:path}")
async def serve_spa(path: str):
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Frontend not built"}