from asyncio import run
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.db.config import register_db
from app.user.routes import router as user_router
from app.essay.routes import router as essay_router
from app.process.routes import router as process_router
from app.goals.routes import process_essays_job, router as goals_router

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting scheduler...", flush=True)
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=lambda: run(process_essays_job()), trigger=CronTrigger.from_crontab('0 0 * * *', 'Europe/Amsterdam'))
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title="SRL API", lifespan=lifespan)
app.include_router(user_router)
app.include_router(essay_router)
app.include_router(process_router)
app.include_router(goals_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_db(app)