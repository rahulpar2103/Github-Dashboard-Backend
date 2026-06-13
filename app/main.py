from fastapi import FastAPI
from app.routers.githubRouter import router as github_router

app=FastAPI()

app.include_router(github_router)

@app.get("/")
def health():
    return {"status":"ok"}