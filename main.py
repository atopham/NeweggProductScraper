from newegg_scraper import scrape_newegg_product, prepare_for_duckdb
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
        # Scrape the product
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
        
        # Get and display database summary
        item_number = result['product']['item_number']
        summary = db.get_product_summary(item_number)
        
        if not summary.empty:
            print("\n🦆 DATABASE SUMMARY")
            print("=" * 50)
            print(f"Actual Reviews in DB: {summary.iloc[0]['actual_reviews']}")
            print(f"Average Rating: {summary.iloc[0]['avg_rating']:.2f}")
            print(f"Verified Reviews: {summary.iloc[0]['verified_reviews']}")
        
        # Export to CSV if enabled
        if Config.EXPORT_CSV:
            os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
            db.export_to_csv(item_number, Config.OUTPUT_DIR)
        
        # Save JSON backup
        # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
        
        # with open(f"{Config.OUTPUT_DIR}/scraped_data_{timestamp}.json", "w") as f:
        #     json.dump(result, f, indent=2)
        
        print(f"\n💾 Data saved:")
        print(f"  Database: {Config.DUCKDB_PATH}")
        # print(f"  JSON backup: {Config.OUTPUT_DIR}/scraped_data_{timestamp}.json")
        if Config.EXPORT_CSV:
            print(f"  CSV exports: {Config.OUTPUT_DIR}/")
        
        print(f"\n✅ Scraping completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main()