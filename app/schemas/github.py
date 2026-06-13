from pydantic import BaseModel


class TrackRepoRequest(BaseModel):
    repo: str


class UntrackRepoRequest(BaseModel):
    repo: str
