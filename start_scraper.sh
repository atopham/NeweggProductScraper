#!/bin/bash

# Check if headless mode is enabled
if [ "$HEADLESS" = "false" ]; then
    echo "🚀 Starting scraper in non-headless mode with virtual display..."
    # Start virtual display
    Xvfb :99 -screen 0 1920x1080x24 &
    export DISPLAY=:99
    echo "✅ Virtual display started on :99"
else
    echo "🚀 Starting scraper in headless mode..."
fi

# Run the Python scraper
exec python main.py 