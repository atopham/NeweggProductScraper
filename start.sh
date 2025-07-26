#!/bin/bash
echo "🚀 Starting Xvfb..."
Xvfb :99 -screen 0 1024x768x24 &
sleep 2
echo "🚀 Starting scraper..."
echo "📋 Configuration:"
echo "  Scraper Type: ${SCRAPER_TYPE:-enhanced}"
echo "  Headless: ${HEADLESS:-false}"
echo "  Max Review Pages: ${MAX_REVIEW_PAGES:-3}"
echo "  User Agent Strategy: ${USER_AGENT_STRATEGY:-weighted}"
echo "  Rate Limit: ${RATE_LIMIT_PER_SECOND:-0.5} req/s"
echo "  Max Workers: ${MAX_WORKERS:-2}"
echo "============================================================"
exec python main.py 