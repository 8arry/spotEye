# SpotEye Apartment Monitor - Cloud Run Deployment
FROM python:3.9-slim

# Install system dependencies for Chrome and ChromeDriver
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for persistence
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV CHROME_BIN=/usr/bin/google-chrome
ENV DISPLAY=:99

# Expose port (Cloud Run requirement)
EXPOSE 8080

# Default command - run as web service for Cloud Scheduler triggers
CMD ["uvicorn", "cloud_service:app", "--host", "0.0.0.0", "--port", "8080"] 