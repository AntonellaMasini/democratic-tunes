from fastapi import FastAPI
from dotenv import load_dotenv
from app.api import auth, rooms, tracks, votes, playback
# Load environment variables from .env
load_dotenv()


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Live Party Mode API up! Try /health "}

@app.get("/health")
async def health():
    return {"ok": True}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(rooms.router, prefix="/rooms", tags=["rooms"])
app.include_router(tracks.router, prefix="/tracks", tags=["tracks"])
app.include_router(votes.router, prefix="/votes", tags=["votes"])
app.include_router(playback.router, tags=["playback"])