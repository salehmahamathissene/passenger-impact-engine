FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
 && apt-get install -y bash \
 && rm -rf /var/lib/apt/lists/*

COPY . .

# Install project + pdf extra + matplotlib (needed by pipeline)
RUN pip install --no-cache-dir -e ".[pdf]" matplotlib

# CI uses /out volume
RUN mkdir -p /out

# IMPORTANT: don't rely on console script generation; run module directly
ENTRYPOINT ["python", "-m", "passenger_impact_engine.cli"]
CMD ["--help"]
