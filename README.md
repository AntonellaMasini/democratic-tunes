# Democrative Tunes! — real-time collaborative playlist voting

Hi! I'm building a tiny but super fun app that lets a group of friends **add songs and vote what plays next** , like a digital democratic jukebox for your house parties! I care a lot about clean APIs, resilient infra, and fast UI loops, so I used FastAPI, Postgres and a lightweight React front end.

**Let’s make music arguments... democratic 🎶 !!!**

This is a WIP and I'm actively shipping. Bear in mind that I'm also learning with this so of course there might be some bugs, but hopefully it will improve as days pass! The core is already live:

* Frontend [https://democratic-tunes.fly.dev](https://democratic-tunes.fly.dev).
* API Base [https://democratic-tunes.vercel.app](https://democratic-tunes.vercel.app)

## What I shipped:

* Create guest users with a friendly display name
* Create a room, get a shareable room code, or join an existing room
* Search and add tracks (mock catalog for now)
* Live queue with votes that influence what plays next
* Now Playing panel
* Advance playback endpoint that is host-only, with a playful message for non-hosts
* Polling that stays smooth in the UI and avoids flicker

---

## Stack

### Backend
* FastAPI (async)
* SQLAlchemy 2.0
* Alembic (migrations)

### Frontend
* React + TypeScript
* Vite
* Ky for HTTP

### Infra
* Fly.io for API
* Vercel for frontend
* CORS configured for cross-site cookies in prod

---

## API Quick Tour

Base: https://democratic-tunes.fly.dev
* `GET /health` simple health check

* `POST /auth/guest` body `{ "display_name": "Anto" }`
Sets a `uid` HttpOnly cookie. Returns `{ user_id, display_name }`.
* `POST /auth/logout`

* `POST /rooms` header `X-User-ID: <uid>` body `{ "name": "My Party" }`
Returns `{ code, id, host_user_id }`.
* `POST /rooms/join` header `X-User-ID: <uid>` body `{ "code": "UZ8293R" }`
Returns `{ room_id, user_id }`.
* `GET /rooms/{code}/now-playing` current item
* `POST /rooms/{code}/advance` host only, moves to next track

* `GET /tracks/rooms/{code}/queue` list queue and status
* `GET /tracks/search?artist_or_title=bad+bunny` search mock catalog
* `POST /tracks/rooms/{code}/tracks` body `{ "track_id": "<id>" }` add to queue

* `POST /votes/rooms/{code}/votes` body `{ "room_track_id": "<id>", "value": 1 | -1 }`


## Run it locally

Prereqs: Python 3.11+, Node 18+, Docker (for Postgres)

1. clone and set up
```
git clone https://github.com/<your-username>/live-party-mode.git
cd live-party-mode
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

2. Database in Docker
```
docker run --name party-db \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=app \
  -e POSTGRES_DB=party \
  -p 5433:5432 -d postgres:16
```

3. env 
Create .env in repo root
```
DATABASE_URL=postgresql://app:app@localhost:5433/party
SQL_ECHO=false
ENV=dev
CROSS_SITE_COOKIES=false
```

4. Migrate then run API
```
alembic upgrade head
uvicorn app.main:app --reload
```

5. Run the frontend
```
cd web
npm i
echo 'VITE_API_BASE=http://127.0.0.1:8000' > .env.local
npm run dev
```
Open the Vite URL from the terminal. Create a guest, create or join a room, add songs, vote, and advance.

---
## Production deploys

### Backend on Fly.io
I used Fly Machines with Dockerfile

Secrets I set for prod:
Backend on Fly.io
```
fly secrets set -a democratic-tunes \
  DATABASE_URL="postgresql://<user>:<pass>@<your-fly-pg-host>:5432/<db>"

fly secrets set -a democratic-tunes \
  ENV=prod CROSS_SITE_COOKIES=true FRONTEND_ORIGIN=https://democratic-tunes.vercel.app
```
Then: `fly deploy -a democratic-tunes`

### Frontend on Vercel
Project root for the frontend is `/democratics-tunes-web`
Build command: `npm run build`
Output: `dist`

Environment variable:
`VITE_API_BASE=http://democratic-tunes.fly.dev`

---

##Extra Notes

* The advance endpoint is host-only by design. In the UI I show a friendly message for non-hosts ;)
* The frontend keeps the layout steady while polling! I avoid spinners that shift the layout and I locked panel heights with scroll where needed.
* I persist uid in a cookie for the API and mirror it in localStorage for header fallback. The room code also persists in localStorage so refreshing keeps you in the room.

---

## Roadmap! What's next to come? 

### Short term
* Real catalog search using Spotify or YouTube Music API
* Room presence and real-time updates with WebSockets
* Smarter vote scoring that rewards early picks and prevents brigading
* Soft delete and audit fields on queue items for better moderation

### Medium term
* Spotify OAuth for the host and optional sync to a real Spotify playlist
* Redis for pub/sub events, caching, and rate limiting
* Room roles: host, co-host, guest
* Better empty states and accessibility polish

### Stretch
* “Party Wrapped” stats at the end of a session
* Mobile PWA with add to home screen
