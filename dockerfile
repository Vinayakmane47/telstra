FROM python:3.11-slim

# Install Chromium and dependencies
RUN apt-get update && \
    apt-get install -y wget unzip curl gnupg2 libglib2.0-0 libnss3 libgconf-2-4 libxss1 libappindicator1 libindicator7 libasound2 libgtk-3-0 libx11-xcb1 libxtst6 && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb

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