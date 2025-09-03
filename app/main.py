import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, playback, rooms, tracks, votes
# Load environment variables from .env
load_dotenv()


app = FastAPI(title="Live Party Mode")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")], # set explicit domains in prod
    allow_credentials=True,     # needed for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

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