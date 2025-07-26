from newegg_scraper import scrape_newegg_product, prepare_for_duckdb
from enhanced_scraper import scrape_newegg_product_enhanced
from duckdb_integration import NeweggDuckDB
from config import Config
# import json
# from datetime import datetime
import os

def main():
    """Main function to scrape Newegg products and store in DuckDB."""
    
    # Print configuration
    Config.print_config()
    
    # Example product URL - you can change this to any Newegg product
    url = "https://www.newegg.com/amd-ryzen-7-9000-series-ryzen-7-9800x3d-granite-ridge-zen-5-socket-am5-desktop-cpu-processor/p/N82E16819113877"
    
    print("🚀 Newegg Product Scraper")
    print("=" * 50)
    print(f"Scraping: {url}")
    print("=" * 50)
    
    # Initialize DuckDB
    db = NeweggDuckDB(Config.DUCKDB_PATH)
    
    try:
        # Choose scraper based on configuration
        if Config.is_enhanced_scraper():
            print("🚀 Using ENHANCED scraper with advanced features...")
            
            # Import enhanced scraper dependencies
            from rate_limiter import RateLimitConfig
            
            # Configure enhanced scraper settings
            rate_config = RateLimitConfig(
                requests_per_second=Config.RATE_LIMIT_PER_SECOND,
                burst_size=3,
                adaptive=True,
                error_threshold=0.1,
                success_threshold=0.9
            )
            
            # Scrape with enhanced features
            result = scrape_newegg_product_enhanced(
                url=url, 
                max_review_pages=Config.get_max_review_pages(),
                headless=Config.HEADLESS,
                user_agent_strategy=Config.USER_AGENT_STRATEGY,
                rate_limit_config=rate_config
            )
            
        else:
            print("📦 Using BASIC scraper...")
            
            # Scrape with basic scraper
            result = scrape_newegg_product(
                url=url, 
                max_review_pages=Config.get_max_review_pages(),
                headless=Config.HEADLESS
            )

        # print("🦆 Result: ", result)
        
        # Prepare data for DuckDB
        # duckdb_data = prepare_for_duckdb(result)

        # print("🦆 DuckDB data: ", duckdb_data)
        
        # Insert data into DuckDB
        db.insert_scraped_data(result)
        
        # Display results
        print("\n📊 SCRAPING RESULTS")
        print("=" * 50)
        print(f"Product: {result['product']['title']}")
        print(f"Brand: {result['product']['brand']}")
        print(f"Price: {result['product']['price']}")
        print(f"Rating: {result['product']['rating']}")
        print(f"Total Reviews: {result['metadata']['total_reviews']}")
        print(f"Review Pages: {result['metadata']['total_review_pages']}")
        
        if Config.is_enhanced_scraper():
            print(f"User Agent: {result['metadata']['user_agent'][:50]}...")
            print(f"Browser Profile: {result['metadata']['browser_profile']}")
        
        # Get and display database summary
        item_number = result['product']['item_number']
        summary = db.get_product_summary(item_number)
        
        print(f"\n📊 DATABASE SUMMARY")
        print("=" * 50)
        print(f"Product Item Number: {item_number}")
        print(f"Total Reviews in DB: {len(summary)}")
        
        # Export to CSV if enabled
        if Config.EXPORT_CSV:
            print(f"\n💾 Exporting to CSV...")
            db.export_to_csv(item_number, Config.OUTPUT_DIR)
            print(f"✅ Data exported to {Config.OUTPUT_DIR}")
        
        print("\n✅ Scraping and database operations completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during scraping: {str(e)}")
        raise e

if __name__ == "__main__":
    main()