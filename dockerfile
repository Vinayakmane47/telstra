FROM python:3.11-slim

# Install Chromium and dependencies
RUN apt-get update && \
    apt-get install -y wget curl gnupg2 unzip \
    chromium chromium-driver && \
    rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Set workdir
WORKDIR /app

COPY . .

# Install Python packages
RUN pip install --no-cache-dir fastapi uvicorn selenium overpy jinja2 python-multipart webdriver_manager

# Expose the FastAPI port
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]