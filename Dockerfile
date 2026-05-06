FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
 && apt-get install -y bash \
 && rm -rf /var/lib/apt/lists/*

# 1. Copy everything first so pip can find pyproject.toml/setup.py
COPY . .

# 2. Install everything
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -e ".[pdf]" matplotlib

# 3. CI uses /out volume
RUN mkdir -p /out

ENTRYPOINT ["python", "-m", "passenger_impact_engine.cli"]
EXPOSE 10000

CMD ["uvicorn", "ai_gateway:app", "--host", "0.0.0.0", "--port", "10000"]
