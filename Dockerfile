FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
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

# Expose port if needed for web interface (optional)
# EXPOSE 8000

# Default command
CMD ["python", "main.py"] 