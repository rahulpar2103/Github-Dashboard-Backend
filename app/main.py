from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers.githubRouter import router as github_router
from app.routers.webSocket import router as ws_router
from app.services.githubService import github_service
from app.core.database import Base, engine
from app.routers.authRouter import router as auth_router


Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    github_service.init_client()
    yield
    await github_service.close()

app = FastAPI(lifespan=lifespan)

app.include_router(github_router)
app.include_router(ws_router)
app.include_router(auth_router)

@app.get("/")
def health():
    return {"status":"ok"}