# Variables
APP = app.main:app
HOST = 127.0.0.1
PORT = 8000

# Run the FastAPI app with auto-reload
run:
	uvicorn $(APP) --reload --host $(HOST) --port $(PORT)

# Run without reload (good for production-like testing)
serve:
	uvicorn $(APP) --host $(HOST) --port $(PORT)

# Format code with black
format:
	black .

# Run lint checks with flake8
lint:
	flake8 .

# Remove __pycache__ and Python artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
