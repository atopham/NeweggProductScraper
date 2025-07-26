import os
from typing import Optional

class Config:
    """Configuration class for the Newegg scraper."""
    
    # Scraper selection
    SCRAPER_TYPE = os.getenv('SCRAPER_TYPE', 'enhanced')  # 'basic' or 'enhanced'
    
    # Database configuration
    DUCKDB_PATH = os.getenv('DUCKDB_PATH', ':memory:')
    
    # Scraper configuration
    HEADLESS = os.getenv('HEADLESS', 'false').lower() == 'true'
    MAX_REVIEW_PAGES = int(os.getenv('MAX_REVIEW_PAGES', '3'))  # 0 = all pages
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '1.0'))  # seconds between requests
    
    # Enhanced scraper specific settings
    USER_AGENT_STRATEGY = os.getenv('USER_AGENT_STRATEGY', 'weighted')  # random, sequential, weighted
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '2'))  # for concurrent scraping
    RATE_LIMIT_PER_SECOND = float(os.getenv('RATE_LIMIT_PER_SECOND', '0.5'))  # for enhanced rate limiting
    
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
    def is_enhanced_scraper(cls) -> bool:
        """Check if enhanced scraper is selected."""
        return cls.SCRAPER_TYPE.lower() == 'enhanced'
    
    @classmethod
    def is_basic_scraper(cls) -> bool:
        """Check if basic scraper is selected."""
        return cls.SCRAPER_TYPE.lower() == 'basic'
    
    @classmethod
    def print_config(cls):
        """Print current configuration."""
        print("🔧 CONFIGURATION")
        print("=" * 50)
        print(f"Scraper Type: {cls.SCRAPER_TYPE.upper()}")
        print(f"Database Path: {cls.DUCKDB_PATH}")
        print(f"Headless Mode: {cls.HEADLESS}")
        print(f"Max Review Pages: {cls.get_max_review_pages() or 'All'}")
        print(f"Request Delay: {cls.REQUEST_DELAY}s")
        print(f"Output Directory: {cls.OUTPUT_DIR}")
        print(f"Export CSV: {cls.EXPORT_CSV}")
        print(f"Log Level: {cls.LOG_LEVEL}")
        
        if cls.is_enhanced_scraper():
            print("\n🚀 ENHANCED SCRAPER SETTINGS:")
            print(f"User Agent Strategy: {cls.USER_AGENT_STRATEGY}")
            print(f"Max Workers: {cls.MAX_WORKERS}")
            print(f"Rate Limit: {cls.RATE_LIMIT_PER_SECOND} req/s")
        
        print("=" * 50) 