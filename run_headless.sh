#!/bin/bash

echo "🚀 Running Newegg Scraper in HEADLESS mode..."
echo "================================================"

# Stop any existing containers
docker-compose down

# Set headless mode and run
export HEADLESS=true
docker-compose up --build

echo "✅ Headless scraping completed!" 