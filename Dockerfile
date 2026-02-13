FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y bash && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --no-cache-dir -e . matplotlib

RUN mkdir -p out

# ✅ Make "pie" the entrypoint so `docker run image simulate ...` works
ENTRYPOINT ["pie"]
CMD ["--help"]
