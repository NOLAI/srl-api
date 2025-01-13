from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.config import register_db
from app.user.routes import router as user_router
from app.essay.routes import router as essay_router
from app.process.routes import router as process_router
from app.goals.routes import router as goals_router

origins = [
    '*'
]

def get_application() -> FastAPI:
    _app = FastAPI(
        title="SRL API",
        description=""
    )
    _app.include_router(user_router)
    _app.include_router(essay_router)
    _app.include_router(process_router)
    _app.include_router(goals_router)
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_db(_app)

    return _app


app = get_application()