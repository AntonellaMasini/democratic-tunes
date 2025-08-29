from fastapi import FastAPI
from dotenv import load_dotenv

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
