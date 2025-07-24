from scraper.newegg_scraper import scrape_newegg_product, prepare_for_duckdb
import json
from datetime import datetime

def main():
    """Main function to scrape Newegg products and prepare data for DuckDB."""
    
    # Example product URL - you can change this to any Newegg product
    url = "https://www.newegg.com/amd-ryzen-7-9000-series-ryzen-7-9800x3d-granite-ridge-zen-5-socket-am5-desktop-cpu-processor/p/N82E16819113877"
    
    print("🚀 Newegg Product Scraper")
    print("=" * 50)
    print(f"Scraping: {url}")
    print("=" * 50)
    
    try:
        # Scrape the product
        # max_review_pages=None will scrape ALL available review pages
        # Set to a number (e.g., 5) to limit the number of pages
        result = scrape_newegg_product(
            url=url, 
            max_review_pages=None,  # None = scrape all available pages
            headless=False  # Set to True for production
        )
        
        # Prepare data for DuckDB
        duckdb_data = prepare_for_duckdb(result)
        
        # Display results
        print("\n📊 SCRAPING RESULTS")
        print("=" * 50)
        print(f"Product: {result['product']['title']}")
        print(f"Brand: {result['product']['brand']}")
        print(f"Price: {result['product']['price']}")
        print(f"Rating: {result['product']['rating']}")
        print(f"Total Reviews: {result['metadata']['total_reviews']}")
        print(f"Review Pages: {result['metadata']['total_review_pages']}")
        
        # Show sample reviews
        # if result['reviews']:
        #     print(f"\n📝 SAMPLE REVIEWS (showing first 3)")
        #     print("-" * 50)
        #     for page_reviews in result['reviews'][:1]:  # First page only
        #         for i, review in enumerate(page_reviews[:3], 1):
        #             print(f"\nReview {i}:")
        #             print(f"  Title: {review['title']}")
        #             print(f"  Rating: {review['rating']}")
        #             print(f"  Author: {review['author']}")
        #             print(f"  Verified: {review['is_verified']}")
        #             print(f"  Date: {review['date']}")
                    
        #             # Show truncated content
        #             content = review['full_content']
        #             if len(content) > 100:
        #                 content = content[:100] + "..."
        #             print(f"  Content: {content}")
        #             print("-" * 30)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save full result
        with open(f"data/scraped_data_{timestamp}.json", "w") as f:
            json.dump(result, f, indent=2)
        
        # Save DuckDB-ready data
        with open(f"data/duckdb_data_{timestamp}.json", "w") as f:
            json.dump(duckdb_data, f, indent=2)
        
        print(f"\n💾 Data saved:")
        print(f"  Full data: data/scraped_data_{timestamp}.json")
        print(f"  DuckDB data: data/duckdb_data_{timestamp}.json")
        
        # Show DuckDB table structure
        # print(f"\n🦆 DUCKDB TABLE STRUCTURE")
        # print("=" * 50)
        
        # if duckdb_data['product_table']:
        #     print("\n📦 PRODUCT TABLE:")
        #     product = duckdb_data['product_table'][0]
        #     for key, value in product.items():
        #         print(f"  {key}: {type(value).__name__} = {value}")
        
        # if duckdb_data['reviews_table']:
        #     print(f"\n📝 REVIEWS TABLE ({len(duckdb_data['reviews_table'])} rows):")
        #     review = duckdb_data['reviews_table'][0]
        #     for key, value in review.items():
        #         print(f"  {key}: {type(value).__name__} = {value}")
        
        print(f"\n✅ Scraping completed successfully!")
        print("🦆 Data is ready for DuckDB insertion!")
        
    except Exception as e:
        print(f"❌ Error during scraping: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()