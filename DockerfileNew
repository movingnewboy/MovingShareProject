# Use official Python slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    busybox \
    python3-lxml \
    pv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency list and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port (for the web server)
EXPOSE 8080

# Run both the web server and the bot using bash -c
CMD bash -c "gunicorn app:app --bind 0.0.0.0:8080 & python3 bot.py"
