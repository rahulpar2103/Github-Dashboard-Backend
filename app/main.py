from fastapi import FastAPI
from app.routers.githubRouter import router as github_router
from app.routers.webSocket import router as ws_router
app=FastAPI()

app.include_router(github_router)
app.include_router(ws_router)

@app.get("/")
def health():
    return {"status":"ok"}