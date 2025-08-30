# Live Party Mode — real-time collaborative playlist voting

A tiny backend that lets a group of friends **add songs and vote what plays next** , like a digital jukebox for your parties!

Powered by FastAPI and PostgreSQL, this backend is all about real-time magic—and I’m so excited to add Redis for even snappier caching and connect with Spotify soon! 

Let’s make music arguments democratic 🎶

---

## Stack

- **FastAPI** (async) · **SQLAlchemy 2.0** (type-annotated models) · **Alembic** (migrations)
- **Postgres** (Docker) · **Redis-ready** (for WebSockets + rate limits later)
- **python-dotenv** for env config

---

## What’s here / What’s next

**MVP (done):**
- Create **guest users**
- Create / **join rooms** (each “room” = one party session)

**Next up (roadmap):**
- Tracks & queue (`room_tracks`)
- Voting (`votes`) + scoring (age bonus + anti-brigading)
- WebSockets (room presence + `queue.updated` broadcasts via Redis Pub/Sub)
- Spotify OAuth (search real tracks) & optional playlist sync
- “Party Wrapped” stats at the end of the session

---

## Quick start

> Prereqs: Python 3.11+, Docker Desktop (for Postgres).  
> If port 5432 is busy on your machine, this setup maps Postgres to **5433** on the host.

```bash
# 1) clone and enter
git clone https://github.com/<your-username>/live-party-mode.git
cd live-party-mode

# 2) create & activate venv
python3 -m venv .venv && source .venv/bin/activate

# 3) install deps
pip install -r requirements.txt

# 4) configure env
cp .env.example .env
# (edit .env if needed; default DATABASE_URL uses host port 5433)

# 5) run Postgres in Docker (container port 5432 -> host 5433)
docker run --name party-db \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=app \
  -e POSTGRES_DB=party \
  -p 5433:5432 -d postgres:16

# 6) apply DB migrations
alembic upgrade head

# 7) start API
uvicorn app.main:app --reload
