from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.config import register_db
from app.user.routes import router as user_router
from app.essay.routes import router as essay_router
from app.process.routes import router as process_router
from app.goals.routes import router as goals_router
from app.questions.routes import router as questions_router

app = FastAPI(title="SRL API")
app.include_router(user_router)
app.include_router(essay_router)
app.include_router(process_router)
app.include_router(goals_router)
app.include_router(questions_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_db(app)