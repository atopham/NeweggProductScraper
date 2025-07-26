#!/usr/bin/env python3
"""
Script to query the DuckDB database directly.
Works with both local and Docker databases.
"""

import argparse
import sys
import os
from duckdb_integration import NeweggDuckDB
from config import Config

def print_dataframe(df, title: str):
    """Print a DataFrame with a title."""
    print(f"\n{title}")
    print("=" * 80)
    if df.empty:
        print("No data found.")
    else:
        print(df.to_string(index=False))
    print("=" * 80)

def main():
    """Main function for database queries."""
    parser = argparse.ArgumentParser(description='Query Newegg DuckDB Database')
    
    parser.add_argument('--db-path', type=str,
                       help='DuckDB database path (overrides DUCKDB_PATH env var)')
    
    parser.add_argument('--list-products', action='store_true',
                       help='List all products in database')
    
    parser.add_argument('--product-summary', type=str,
                       help='Get summary for specific product (item number)')
    
    parser.add_argument('--reviews', type=str,
                       help='Get reviews for specific product (item number)')
    
    parser.add_argument('--rating-distribution', type=str,
                       help='Get rating distribution for specific product (item number)')
    
    parser.add_argument('--search', nargs=2, metavar=('ITEM_NUMBER', 'SEARCH_TERM'),
                       help='Search reviews for specific terms')
    
    parser.add_argument('--recent-reviews', nargs=2, metavar=('ITEM_NUMBER', 'LIMIT'),
                       help='Get recent reviews (item_number limit)')
    
    parser.add_argument('--high-rated', nargs=2, metavar=('ITEM_NUMBER', 'MIN_RATING'),
                       help='Get high-rated reviews (item_number min_rating)')
    
    parser.add_argument('--export-csv', type=str,
                       help='Export data to CSV (item_number)')
    
    parser.add_argument('--docker', action='store_true',
                       help='Use Docker database path (/app/data/newegg_data.duckdb)')
    
    args = parser.parse_args()
    
    # Set database path
    if args.docker:
        # Use Docker path
        db_path = "/app/data/newegg_data.duckdb"
        print(f"🐳 Using Docker database path: {db_path}")
    elif args.db_path:
        # Use explicit path
        db_path = args.db_path
        print(f"📁 Using explicit database path: {db_path}")
    else:
        # Use environment variable or default
        # db_path = os.getenv('DUCKDB_PATH', ':memory:')
        db_path = Config.DUCKDB_PATH
        print(f"🔧 Using database path: {db_path}")
    
    # Initialize database
    try:
        db = NeweggDuckDB(db_path)
        print(f"🦆 Connected to database: {db.db_path}")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
        print("\n💡 Troubleshooting tips:")
        print("  - Use --docker flag for Docker environment")
        print("  - Use --db-path to specify custom path")
        print("  - Check if database file exists")
        print("  - Ensure proper file permissions")
        sys.exit(1)
    
    try:
        # List all products
        if args.list_products:
            products = db.get_product_summary()
            print_dataframe(products, "📦 ALL PRODUCTS")
        
        # Product summary
        elif args.product_summary:
            summary = db.get_product_summary(args.product_summary)
            print_dataframe(summary, f"📊 PRODUCT SUMMARY: {args.product_summary}")
        
        # Reviews
        elif args.reviews:
            reviews_query = """
                SELECT title, rating, author, date, is_verified, 
                       SUBSTR(full_content, 1, 200) as content_preview
                FROM reviews 
                WHERE product_item_number = ?
                ORDER BY date DESC
                LIMIT 20
            """
            reviews = db.conn.execute(reviews_query, [args.reviews]).df()
            print_dataframe(reviews, f"📝 REVIEWS: {args.reviews}")
        
        # Rating distribution
        elif args.rating_distribution:
            ratings = db.get_rating_distribution(args.rating_distribution)
            print_dataframe(ratings, f"⭐ RATING DISTRIBUTION: {args.rating_distribution}")
        
        # Search reviews
        elif args.search:
            item_number, search_term = args.search
            results = db.search_reviews(item_number, search_term)
            print_dataframe(results, f"🔍 SEARCH RESULTS for '{search_term}' in {item_number}")
        
        # Recent reviews
        elif args.recent_reviews:
            item_number, limit = args.recent_reviews
            recent = db.get_recent_reviews(item_number, int(limit))
            print_dataframe(recent, f"🕒 RECENT REVIEWS: {item_number} (last {limit})")
        
        # High-rated reviews
        elif args.high_rated:
            item_number, min_rating = args.high_rated
            high_rated = db.get_reviews_by_rating(item_number, int(min_rating))
            print_dataframe(high_rated, f"🔥 HIGH-RATED REVIEWS: {item_number} ({min_rating}+ stars)")
        
        # Export to CSV
        elif args.export_csv:
            print(f"💾 Exporting data for {args.export_csv}...")
            db.export_to_csv(args.export_csv, ".")
            print("✅ Export completed!")
        
        else:
            # No arguments provided, show help
            parser.print_help()
            print("\n💡 Quick examples:")
            print("  python query_db.py --docker --list-products")
            print("  python query_db.py --docker --product-summary N82E16819113877")
            print("  python query_db.py --docker --reviews N82E16819113877")
            print("  python query_db.py --docker --search N82E16819113877 performance")
    
    except Exception as e:
        print(f"❌ Error during query: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 