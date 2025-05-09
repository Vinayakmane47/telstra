FROM python:3.11-slim

# Install system dependencies and Google Chrome
RUN apt-get update && \
    apt-get install -y wget unzip curl gnupg2 \
        libglib2.0-0 libnss3 libgconf-2-4 libxss1 \
        libappindicator1 libindicator7 libasound2 \
        libgtk-3-0 libx11-xcb1 libxtst6 fonts-liberation libu2f-udev \
        ca-certificates gnupg lsb-release && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && \
    apt-get clean

# Set environment variable to use Chrome
ENV CHROME_BIN="/usr/bin/google-chrome"

# Set working directory
WORKDIR /app

# Copy app code
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi uvicorn selenium overpy jinja2 python-multipart webdriver-manager

# Expose port for FastAPI
EXPOSE 8000

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
