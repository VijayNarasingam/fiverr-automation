from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api import analytics, gigs, health, logs, messages, orders, sse
from app.api.settings import router as settings_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(settings.DATABASE_URL)
    yield


app = FastAPI(title="Fiverr Automation Agent", lifespan=lifespan)

app.include_router(health.router)
app.include_router(gigs.router)
app.include_router(orders.router)
app.include_router(messages.router)
app.include_router(analytics.router)
app.include_router(settings_router)
app.include_router(logs.router)
app.include_router(sse.router)
