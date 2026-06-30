from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers.githubRouter import router as github_router
from app.routers.webSocket import router as ws_router
from app.services.githubService import github_service
from app.core.database import Base, engine
from app.routers.authRouter import router as auth_router
from app.core.security import http_bearer

Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    github_service.init_client()
    yield
    await github_service.close()

app = FastAPI(lifespan=lifespan, dependencies=[Depends(http_bearer)])

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(github_router)
app.include_router(ws_router)
app.include_router(auth_router)

@app.get("/")
def health():
    return {"status":"ok"}