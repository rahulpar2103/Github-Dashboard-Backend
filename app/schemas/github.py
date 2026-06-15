from pydantic import BaseModel

class TrackRepoRequest(BaseModel):
    repo: str
    user_id: str = "0"

class UntrackRepoRequest(BaseModel):
    repo: str
    user_id: str = "0"
