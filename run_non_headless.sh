#!/bin/bash

echo "🚀 Running Newegg Scraper in NON-HEADLESS mode with virtual display..."
echo "====================================================================="

# Stop any existing containers
docker-compose down

# Set non-headless mode and run
export HEADLESS=false
docker-compose up --build

echo "✅ Non-headless scraping completed!" 