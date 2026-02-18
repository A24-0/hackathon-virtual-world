from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from app.db.database import connect, disconnect
from app.controllers.system_controller import router as system_router
from app.controllers.text_controller import router as text_router
from app.controllers.action_controller import router as action_router
from app.controllers.logger_controller import router as logger_router
from app.services.lifecycle_service import run_lifecycle_loop
from app.services.seed_agents import seed_initial_agents


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    # Создаем базовых агентов, если их еще нет
    await seed_initial_agents()
    # Запускаем фоновый цикл жизнедеятельности агентов
    lifecycle_task = asyncio.create_task(run_lifecycle_loop())
    yield
    lifecycle_task.cancel()
    try:
        await lifecycle_task
    except asyncio.CancelledError:
        pass
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

app.include_router(system_router, prefix="/api/v1")
app.include_router(text_router, prefix="/api/v1")
app.include_router(action_router, prefix="/api/v1")
app.include_router(logger_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"service": "Virtual World API", "version": "2.0.0"}
