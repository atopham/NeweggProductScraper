# Newegg Product Scraper

A web scraper for Newegg products that extracts product information and reviews, storing data in DuckDB for analysis.

## Features

- 🕷️ **Web Scraping**: Scrapes product details and reviews from Newegg
- 🦆 **DuckDB Integration**: Stores data in embedded DuckDB database
- 📊 **Data Analysis**: Built-in queries for product summaries and review analysis
- 🐳 **Docker Support**: Containerized for easy deployment
- 📁 **Multiple Output Formats**: JSON, CSV, and database storage
- ⚙️ **Configurable**: Environment variables and command-line options

## Quick Start

### Prerequisites

- **Python 3.8+** (3.9+ recommended)
- **Git** (for cloning the repository)
- **Chrome/Chromium browser** (for Playwright)
- **pip** (Python package installer)

### Local Development

1. **Clone the repository**:
   ```bash
   git clone git@github.com:atopham/NeweggProductScraper.git
   cd newegg_scraper
   ```

2. **Create and activate virtual environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

5. **Set up environment variables** (optional):
   ```bash
   # The necessary env variables have defaults but if you want specific values, you can set them

   export DUCKDB_PATH="./data/newegg_data.duckdb"
   export MAX_REVIEW_PAGES="3"
   export SCRAPER_TYPE="enhanced"
   ```

6. **Run the scraper**:
   ```bash
   python main.py
   ```

### Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Or build and run manually**:
   ```bash
   docker build -t newegg-scraper .
   docker run -v $(pwd)/data:/app/data newegg-scraper
   ```

## Configuration

### Environment Variables

The scraper can be configured using environment variables. You can set these in your shell, create a `.env` file, or pass them when running Docker.

#### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `SCRAPER_TYPE` | `enhanced` | Scraper type: `basic` or `enhanced` |
| `DUCKDB_PATH` | `./data/newegg_data.duckdb` | DuckDB database path |
| `HEADLESS` | `false` | Run browser in headless mode |
| `MAX_REVIEW_PAGES` | `3` | Max review pages to scrape (0 = all) |
| `REQUEST_DELAY` | `1.0` | Delay between requests (seconds) |

#### Enhanced Scraper Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `USER_AGENT_STRATEGY` | `weighted` | User agent rotation: `random`, `sequential`, `weighted` |
| `MAX_WORKERS` | `2` | Number of concurrent workers |
| `RATE_LIMIT_PER_SECOND` | `0.5` | Requests per second limit |

#### Output Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTPUT_DIR` | `./data` | Output directory for files |
| `EXPORT_CSV` | `false` | Export data to CSV files |

#### Logging Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FILE` | `./logs/scraper.log` | Log file path |

### Environment Setup Examples

#### Local Development (.env file)
```bash
# Create .env file in project root
SCRAPER_TYPE=enhanced
DUCKDB_PATH=./data/newegg_data.duckdb
HEADLESS=false
MAX_REVIEW_PAGES=6
USER_AGENT_STRATEGY=weighted
RATE_LIMIT_PER_SECOND=0.5
EXPORT_CSV=true
LOG_LEVEL=INFO
```

#### Production Settings
```bash
SCRAPER_TYPE=enhanced
DUCKDB_PATH=/app/data/newegg_data.duckdb
HEADLESS=true
MAX_REVIEW_PAGES=10
USER_AGENT_STRATEGY=random
RATE_LIMIT_PER_SECOND=0.3
EXPORT_CSV=false
LOG_LEVEL=WARNING
```

#### Quick Testing
```bash
SCRAPER_TYPE=basic
DUCKDB_PATH=:memory:
HEADLESS=true
MAX_REVIEW_PAGES=1
EXPORT_CSV=false
```

### Command Line Options

```bash
python run_scraper.py --help
```

Options:
- `--url`: Newegg product URL to scrape
- `--db-path`: DuckDB database path
- `--headless`: Run browser in headless mode
- `--max-pages`: Maximum review pages to scrape
- `--output-dir`: Output directory
- `--no-csv`: Skip CSV export
- `--config-only`: Print configuration and exit

## Database Schema

### Products Table
- `item_number` (VARCHAR, PRIMARY KEY)
- `title` (VARCHAR)
- `brand` (VARCHAR)
- `price` (VARCHAR)
- `rating` (VARCHAR)
- `reviews_count` (VARCHAR)
- `description` (TEXT)
- `product_url` (VARCHAR)
- `scraped_at` (TIMESTAMP)

### Reviews Table
- `review_id` (VARCHAR, PRIMARY KEY)
- `product_item_number` (VARCHAR)
- `page_number` (INTEGER)
- `review_index` (INTEGER)
- `title` (VARCHAR)
- `rating` (VARCHAR)
- `author` (VARCHAR)
- `date` (VARCHAR)
- `is_verified` (BOOLEAN)
- `ownership` (VARCHAR)
- `pros` (TEXT)
- `cons` (TEXT)
- `overall_review` (TEXT)
- `full_content` (TEXT)
- `timestamp` (TIMESTAMP)

### Metadata Table
- `product_url` (VARCHAR, PRIMARY KEY)
- `scraped_at` (TIMESTAMP)
- `total_review_pages` (INTEGER)
- `total_reviews` (INTEGER)
- `scraper_version` (VARCHAR)

## Usage Examples

### Basic Scraping
```python
from duckdb_integration import NeweggDuckDB

# Initialize database
db = NeweggDuckDB("my_data.duckdb")

# Get product summary
summary = db.get_product_summary("N82E16819113877")
print(summary)

# Get high-rated reviews
reviews = db.get_reviews_by_rating("N82E16819113877", min_rating=4)
print(reviews)

# Search reviews
results = db.search_reviews("N82E16819113877", "performance")
print(results)
```

### Docker Examples

**Run with persistent storage**:
```bash
docker run -v $(pwd)/data:/app/data \
  -e DUCKDB_PATH=/app/data/newegg_data.duckdb \
  -e HEADLESS=true \
  newegg-scraper
```

**Run with custom configuration**:
```bash
docker run -v $(pwd)/data:/app/data \
  -e DUCKDB_PATH=/app/data/newegg_data.duckdb \
  -e HEADLESS=true \
  -e MAX_REVIEW_PAGES=10 \
  -e EXPORT_CSV=true \
  newegg-scraper
```

## Data Persistence

### Local Development
- Database files are stored in the specified path
- Use `:memory:` for temporary testing
- Use file paths for persistent storage

### Docker
- Mount volumes to persist data between container runs
- Database files are stored in the mounted volume
- Data survives container restarts

## File Structure

```
newegg_scraper/
├── scraper/
│   └── newegg_scraper.py      # Main scraping logic
├── duckdb_integration.py      # Database operations
├── config.py                  # Configuration management
├── main.py                    # Main execution script
├── run_scraper.py            # CLI interface
├── requirements.txt           # Python dependencies
├── Dockerfile                # Docker image definition
├── docker-compose.yml        # Docker Compose configuration
├── .dockerignore             # Docker build exclusions
└── data/                     # Output directory (created automatically)
```

## Development

### Development Workflow

1. **Set up development environment**:
   ```bash
   # Clone and setup
   git clone <repository-url>
   cd newegg_scraper
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   playwright install chromium
   
   # Create development config
   cp .env.example .env  # if available
   ```

2. **Run in development mode**:
   ```bash
   # Use basic scraper for faster development
   export SCRAPER_TYPE=basic
   export HEADLESS=false  # See browser in action
   export MAX_REVIEW_PAGES=1  # Quick testing
   
   python main.py
   ```

3. **Test enhanced features**:
   ```bash
   # Test enhanced scraper
   export SCRAPER_TYPE=enhanced
   export HEADLESS=true
   export MAX_REVIEW_PAGES=3
   
   python main.py
   ```

### Adding New Queries
Extend the `NeweggDuckDB` class with new methods:

```python
def get_reviews_by_date_range(self, item_number: str, start_date: str, end_date: str):
    query = """
        SELECT * FROM reviews 
        WHERE product_item_number = ? 
        AND date BETWEEN ? AND ?
        ORDER BY date DESC
    """
    return self.conn.execute(query, [item_number, start_date, end_date]).df()
```

### Customizing Scraping
Modify `scraper/newegg_scraper.py` to:
- Add new data fields
- Change scraping logic
- Add new data sources

### Best Practices

1. **Always use virtual environments** for development
2. **Test with small datasets** first (set `MAX_REVIEW_PAGES=1`)
3. **Use headless mode** for production, visible mode for debugging
4. **Monitor rate limits** to avoid being blocked
5. **Backup your database** before major changes
6. **Use environment variables** for configuration
7. **Test both basic and enhanced scrapers** before deploying

## Troubleshooting

### Common Issues

#### Setup Issues

1. **Python version issues**:
   ```bash
   # Check Python version
   python --version
   # Should be 3.8+ (3.9+ recommended)
   ```

2. **Virtual environment not activated**:
   ```bash
   # Make sure you see (venv) in your prompt
   # If not, activate it:
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

3. **Playwright browser not installed**:
   ```bash
   # Install Playwright browsers
   playwright install chromium
   # Or install all browsers
   playwright install
   ```

4. **Permission errors on macOS/Linux**:
   ```bash
   # Fix permissions for data directory
   mkdir -p data logs
   chmod 755 data logs
   ```

#### Runtime Issues

1. **Chrome/ChromeDriver issues in Docker**:
   - Ensure Chrome is properly installed in the Docker image
   - Use headless mode for Docker environments

2. **Database permission errors**:
   - Check file permissions for the database directory
   - Ensure the directory exists and is writable

3. **Memory issues with large datasets**:
   - Use file-based database instead of in-memory
   - Limit the number of review pages scraped

4. **Rate limiting/blocking**:
   ```bash
   # Reduce rate limit
   export RATE_LIMIT_PER_SECOND=0.2
   # Use basic scraper
   export SCRAPER_TYPE=basic
   ```

5. **Network connectivity issues**:
   ```bash
   # Test connectivity
   curl -I https://www.newegg.com
   # Check if behind corporate firewall/proxy
   ```

### Logs
- Check console output for detailed error messages
- Use `LOG_LEVEL=DEBUG` for verbose logging
- Logs are written to `./logs/scraper.log` when configured

## License

This project is for educational purposes. Please respect Newegg's terms of service and robots.txt when scraping.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request 