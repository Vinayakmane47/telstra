# -------------------------
# Dockerfile for 5G Checker Web App
# -------------------------

FROM python:3.11-slim

# Install system packages and Chrome
RUN apt-get update && \
    apt-get install -y wget curl unzip gnupg2 chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables for Chrome
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy all app files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn selenium overpy jinja2

# Expose FastAPI port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]