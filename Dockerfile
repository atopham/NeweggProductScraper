FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Xvfb for virtual display
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    xvfb \
    x11-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Chrome and ChromeDriver for Selenium
# Handle both AMD64 and ARM64 architectures
RUN if [ "$(uname -m)" = "x86_64" ]; then \
        wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
        && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
        && apt-get update \
        && apt-get install -y google-chrome-stable; \
    else \
        # For ARM64 (Apple Silicon), install Chromium instead
        apt-get update \
        && apt-get install -y chromium \
        && ln -s /usr/bin/chromium /usr/bin/google-chrome-stable; \
    fi \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install Playwright browsers
RUN playwright install chromium

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Set environment variables
ENV DUCKDB_PATH=/app/data/newegg_data.duckdb
ENV PYTHONPATH=/app
ENV DISPLAY=:99

# Expose port if needed for web interface (optional)
# EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
echo "🚀 Starting Xvfb..."\n\
Xvfb :99 -screen 0 1024x768x24 &\n\
sleep 2\n\
echo "🚀 Starting scraper..."\n\
exec python main.py' > /app/start.sh && chmod +x /app/start.sh

# Default command - use startup script
CMD ["/app/start.sh"] 