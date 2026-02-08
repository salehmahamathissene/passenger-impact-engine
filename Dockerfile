FROM python:3.12-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y bash && rm -rf /var/lib/apt/lists/*

# Copy project
COPY . .

# Install python package + dependencies
RUN pip install --no-cache-dir -e .

# Render uses PORT automatically
ENV PYTHONPATH=src

# Start FastAPI correctly
CMD bash -lc "uvicorn pie.main:app --host 0.0.0.0 --port ${PORT:-8000}"
