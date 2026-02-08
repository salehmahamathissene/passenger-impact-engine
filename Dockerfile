FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y bash && rm -rf /var/lib/apt/lists/*

COPY . .

# Install package + dependencies (this will now include fastapi/uvicorn from pyproject)
RUN pip install --no-cache-dir -e .

# CLI container by default (THIS is what your CI expects)
ENTRYPOINT ["pie"]
CMD ["--help"]
