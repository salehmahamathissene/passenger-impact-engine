FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (including for matplotlib)
RUN apt-get update && apt-get install -y \
    bash \
    && rm -rf /var/lib/apt/lists/*

# Copy application code first (for better caching)
COPY . .

# Install the package with matplotlib
RUN pip install --no-cache-dir -e . matplotlib

# Make sure the out directory exists
RUN mkdir -p out

# Set working directory
WORKDIR /app

# Default command
CMD ["pie", "--help"]
