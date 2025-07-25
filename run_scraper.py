#!/usr/bin/env python3
"""
Script to run the Newegg scraper with different configurations.
Supports command line arguments and environment variables.
"""

import argparse
import os
import sys
from main import main as run_main
from config import Config

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Newegg Product Scraper')
    
    parser.add_argument('--url', type=str, 
                       default="https://www.newegg.com/amd-ryzen-7-9000-series-ryzen-7-9800x3d-granite-ridge-zen-5-socket-am5-desktop-cpu-processor/p/N82E16819113877",
                       help='Newegg product URL to scrape')
    
    parser.add_argument('--db-path', type=str,
                       help='DuckDB database path (overrides DUCKDB_PATH env var)')
    
    parser.add_argument('--headless', action='store_true',
                       help='Run browser in headless mode')
    
    parser.add_argument('--max-pages', type=int, default=0,
                       help='Maximum review pages to scrape (0 = all pages)')
    
    parser.add_argument('--output-dir', type=str, default='./data',
                       help='Output directory for data files')
    
    parser.add_argument('--no-csv', action='store_true',
                       help='Skip CSV export')
    
    parser.add_argument('--config-only', action='store_true',
                       help='Only print configuration and exit')
    
    return parser.parse_args()

def set_environment_from_args(args):
    """Set environment variables from command line arguments."""
    if args.db_path:
        os.environ['DUCKDB_PATH'] = args.db_path
    
    if args.headless:
        os.environ['HEADLESS'] = 'true'
    
    if args.max_pages != 0:
        os.environ['MAX_REVIEW_PAGES'] = str(args.max_pages)
    
    if args.output_dir:
        os.environ['OUTPUT_DIR'] = args.output_dir
    
    if args.no_csv:
        os.environ['EXPORT_CSV'] = 'false'

def main():
    """Main function."""
    args = parse_arguments()
    
    # Set environment variables from arguments
    set_environment_from_args(args)
    
    # Print configuration
    print("🔧 SCRAPER CONFIGURATION")
    print("=" * 50)
    print(f"URL: {args.url}")
    Config.print_config()
    
    if args.config_only:
        print("Configuration printed. Exiting.")
        return
    
    # Update the URL in the main function (you might want to modify main.py to accept URL as parameter)
    print(f"\n🚀 Starting scraper for: {args.url}")
    print("=" * 50)
    
    # For now, you'll need to manually update the URL in main.py
    # In a more sophisticated setup, you could modify main.py to accept URL as parameter
    print("Note: To use a different URL, please update the URL in main.py")
    print("or modify the scraper to accept URL as a parameter.")
    
    # Run the scraper
    try:
        run_main()
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 