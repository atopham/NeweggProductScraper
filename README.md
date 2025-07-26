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

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the scraper**:
   ```bash
   python main.py
   ```

3. **Or use the configuration script**:
   ```bash
   python run_scraper.py --max-pages 5
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

| Variable | Default | Description |
|----------|---------|-------------|
| `DUCKDB_PATH` | `:memory:` | DuckDB database path |
| `HEADLESS` | `false` | Run browser in headless mode |
| `MAX_REVIEW_PAGES` | `0` | Max review pages to scrape (0 = all) |
| `REQUEST_DELAY` | `1.0` | Delay between requests (seconds) |
| `OUTPUT_DIR` | `./data` | Output directory for files |
| `EXPORT_CSV` | `true` | Export data to CSV files |

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

## Troubleshooting

### Common Issues

1. **Chrome/ChromeDriver issues in Docker**:
   - Ensure Chrome is properly installed in the Docker image
   - Use headless mode for Docker environments

2. **Database permission errors**:
   - Check file permissions for the database directory
   - Ensure the directory exists and is writable

3. **Memory issues with large datasets**:
   - Use file-based database instead of in-memory
   - Limit the number of review pages scraped

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