import os
from typing import Optional

class Config:
    """Configuration class for the Newegg scraper."""
    
    # Database configuration
    DUCKDB_PATH = os.getenv('DUCKDB_PATH', ':memory:')
    
    # Scraper configuration
    HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
    MAX_REVIEW_PAGES = int(os.getenv('MAX_REVIEW_PAGES', '3'))  # 0 = all pages
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '1.0'))  # seconds between requests
    
    # Output configuration
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './data')
    EXPORT_CSV = os.getenv('EXPORT_CSV', 'false').lower() == 'true'
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/scraper.log')
    
    @classmethod
    def get_max_review_pages(cls) -> Optional[int]:
        """Get max review pages, returning None if set to 0 (all pages)."""
        return None if cls.MAX_REVIEW_PAGES == 0 else cls.MAX_REVIEW_PAGES
    
    @classmethod
    def print_config(cls):
        """Print current configuration."""
        print("🔧 CONFIGURATION")
        print("=" * 50)
        print(f"Database Path: {cls.DUCKDB_PATH}")
        print(f"Headless Mode: {cls.HEADLESS}")
        print(f"Max Review Pages: {cls.get_max_review_pages() or 'All'}")
        print(f"Request Delay: {cls.REQUEST_DELAY}s")
        print(f"Output Directory: {cls.OUTPUT_DIR}")
        print(f"Export CSV: {cls.EXPORT_CSV}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        print("=" * 50) 