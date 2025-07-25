#!/usr/bin/env python3
"""
Script to query the DuckDB database directly.
Works with both local and Docker databases.
"""

import argparse
import os
import sys
from duckdb_integration import NeweggDuckDB
from config import Config
import pandas as pd

def print_dataframe(df, title=""):
    """Pretty print a DataFrame."""
    if title:
        print(f"\n{title}")
        print("=" * 50)
    
    if df.empty:
        print("No data found.")
    else:
        print(df.to_string(index=False))

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
    
    args = parser.parse_args()
    
    # Set database path
    if args.db_path:
        os.environ['DUCKDB_PATH'] = args.db_path
    
    # Initialize database
    try:
        db = NeweggDuckDB()
        print(f"🦆 Connected to database: {db.db_path}")
    except Exception as e:
        print(f"❌ Error connecting to database: {e}")
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
            db.export_to_csv(args.export_csv)
            print(f"✅ Exported data for {args.export_csv} to CSV files")
        
        # Default: show available commands
        else:
            print("🔍 DATABASE QUERY TOOL")
            print("=" * 50)
            print("Available commands:")
            print("  --list-products                    List all products")
            print("  --product-summary ITEM_NUMBER     Get product summary")
            print("  --reviews ITEM_NUMBER             Get recent reviews")
            print("  --rating-distribution ITEM_NUMBER Get rating distribution")
            print("  --search ITEM_NUMBER TERM         Search reviews")
            print("  --recent-reviews ITEM_NUMBER LIMIT Get recent reviews")
            print("  --high-rated ITEM_NUMBER MIN_RATING Get high-rated reviews")
            print("  --export-csv ITEM_NUMBER          Export to CSV")
            print("\nExamples:")
            print("  python query_db.py --list-products")
            print("  python query_db.py --product-summary N82E16819113877")
            print("  python query_db.py --search N82E16819113877 performance")
            print("  python query_db.py --high-rated N82E16819113877 4")
    
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    main() 