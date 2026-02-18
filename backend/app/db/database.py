from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.agent import Agent
from app.models.event import Event
from app.models.log import Log
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DATABASE_NAME", "virtual_world")

client: AsyncIOMotorClient = None


async def connect():
    global client
    client = AsyncIOMotorClient(MONGODB_URL)
    await init_beanie(database=client[DB_NAME], document_models=[Agent, Event, Log])
    print(f"MongoDB connected: {DB_NAME}")


async def disconnect():
    global client
    if client:
        client.close()
