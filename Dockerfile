# Tell Docker how to build a container image for my Python app

FROM python:3.12-slim

# install system deps and cleans cache to keep image small
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Sets the working dir inside the container to /app
WORKDIR /app

# deps first , if dependencies don’t change, docker reuses layers speeding up builds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy entire app into the container under /app
COPY . .

# Sets env variables inside the container
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# when the container starts, this runs migrations (alembic upgrade head) to update the database schema, 
# then starts the server with Gunicorn using Uvicorn workers on the specified port
# - Gunicorn alone doesn’t support async apps well, Gunicorn is like concert manager
# - Uvicorn alone doesn’t handle process management (multiple workers), Uvicorn is like one of the bands that actually performs the music (runs async Python code)
CMD ["bash", "-lc", "alembic upgrade head && gunicorn -k uvicorn.workers.UvicornWorker 'app.main:app' --bind 0.0.0.0:${PORT} --workers 2 --timeout 60"]