# -------------------------
# Dockerfile for 5G Checker
# -------------------------

FROM python:3.11-slim

# Install required system packages
RUN apt-get update && \
    apt-get install -y wget curl gnupg2 unzip && \
    rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /app

# Copy Python script into container
COPY main.py .

# Install Python dependencies
RUN pip install --no-cache-dir selenium overpy webdriver-manager

# Entry point with arguments: workers, latitude, longitude, count
ENTRYPOINT ["python", "main.py"]