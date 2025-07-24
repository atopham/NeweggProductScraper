import duckdb
import json
from datetime import datetime
from typing import Dict
import pandas as pd

class NeweggDuckDB:
    """
    DuckDB integration for Newegg scraped data.
    Handles data insertion, querying, and analysis.
    """
    
    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize DuckDB connection.
        
        Args:
            db_path: Path to DuckDB file (use ":memory:" for in-memory database)
        """
        self.conn = duckdb.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create the necessary tables for Newegg data."""
        
        # Products table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                item_number VARCHAR PRIMARY KEY,
                title VARCHAR,
                brand VARCHAR,
                price VARCHAR,
                rating VARCHAR,
                reviews_count VARCHAR,
                description TEXT,
                product_url VARCHAR,
                scraped_at TIMESTAMP
            )
        """)
        
        # Reviews table (denormalized for easier querying)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                review_id VARCHAR PRIMARY KEY,
                product_item_number VARCHAR,
                page_number INTEGER,
                review_index INTEGER,
                title VARCHAR,
                rating VARCHAR,
                author VARCHAR,
                date VARCHAR,
                is_verified BOOLEAN,
                ownership VARCHAR,
                pros TEXT,
                cons TEXT,
                overall_review TEXT,
                full_content TEXT,
                timestamp TIMESTAMP,
            )
        """)
            # -- Product info (denormalized)
            # product_url VARCHAR,
            # product_title VARCHAR,
            # product_brand VARCHAR,
            # product_price VARCHAR,
            # product_rating VARCHAR,
            # product_reviews_count VARCHAR,
            # product_item_number VARCHAR,
            # scraped_at TIMESTAMP
        
        # Metadata table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scraping_metadata (
                product_url VARCHAR PRIMARY KEY,
                scraped_at TIMESTAMP,
                total_review_pages INTEGER,
                total_reviews INTEGER,
                scraper_version VARCHAR
            )
        """)
        
        print("✅ DuckDB tables created successfully")
    
    def insert_scraped_data(self, scraped_data: Dict):
        """
        Insert scraped data into DuckDB tables.
        
        Args:
            scraped_data: Data from scrape_newegg_product function
        """
        try:
            # Insert product data
            product = scraped_data["product"]
            self.conn.execute("""
                INSERT OR REPLACE INTO products 
                (item_number, title, brand, price, rating, reviews_count, description, product_url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                product["item_number"],
                product["title"],
                product["brand"],
                product["price"],
                product["rating"],
                product["reviews_count"],
                product["description"],
                product["product_url"],
                datetime.fromisoformat(scraped_data["metadata"]["scraped_at"])
            ])
            
            # Insert reviews data
            reviews = scraped_data["reviews"]
            for page_reviews in reviews:
                for review in page_reviews:
                    self.conn.execute("""
                        INSERT OR REPLACE INTO reviews 
                        (review_id, product_item_number, page_number, review_index, title, rating, author, date, 
                         is_verified, ownership, pros, cons, overall_review, full_content, 
                         timestamp, product_url, product_title, product_brand, product_price,
                         product_rating, product_reviews_count, product_item_number, scraped_at) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        review["review_id"],
                        product["item_number"],
                        review["page_number"],
                        review["review_index"],
                        review["title"],
                        review["rating"],
                        review["author"],
                        review["date"],
                        review["is_verified"],
                        review["ownership"],
                        review["pros"],
                        review["cons"],
                        review["overall_review"],
                        review["full_content"],
                        datetime.fromisoformat(review["timestamp"]),
                        scraped_data["metadata"]["product_url"],
                        # product["title"],
                        # product["brand"],
                        # product["price"],
                        # product["rating"],
                        # product["reviews_count"],
                        # product["item_number"],
                        datetime.fromisoformat(scraped_data["metadata"]["scraped_at"])
                    ])
            
            # Insert metadata
            metadata = scraped_data["metadata"]
            self.conn.execute("""
                INSERT OR REPLACE INTO scraping_metadata 
                (product_url, scraped_at, total_review_pages, total_reviews, scraper_version)
                VALUES (?, ?, ?, ?, ?)
            """, [
                metadata["product_url"],
                datetime.fromisoformat(metadata["scraped_at"]),
                metadata["total_review_pages"],
                metadata["total_reviews"],
                metadata["scraper_version"]
            ])
            
            print(f"✅ Successfully inserted data for {product['title']}")
            print(f"   - {metadata['total_reviews']} reviews")
            print(f"   - {metadata['total_review_pages']} pages")
            
        except Exception as e:
            print(f"❌ Error inserting data: {e}")
            raise
    
    def get_product_summary(self, item_number: str = None) -> pd.DataFrame:
        """
        Get summary statistics for products.
        
        Args:
            item_number: Specific product item number (None for all products)
        
        Returns:
            DataFrame with product summary
        """
        if item_number:
            query = """
                SELECT 
                    p.item_number,
                    p.title,
                    p.brand,
                    p.price,
                    p.rating,
                    p.reviews_count,
                    COUNT(r.review_id) as actual_reviews,
                    AVG(CAST(SUBSTR(r.rating, 1, 1) AS INTEGER)) as avg_rating,
                    COUNT(CASE WHEN r.is_verified = true THEN 1 END) as verified_reviews,
                    p.scraped_at
                FROM products p
                LEFT JOIN reviews r ON p.item_number = r.product_item_number
                WHERE p.item_number = ?
                GROUP BY p.item_number, p.title, p.brand, p.price, p.rating, p.reviews_count, p.scraped_at
            """
            return self.conn.execute(query, [item_number]).df()
        else:
            query = """
                SELECT 
                    p.item_number,
                    p.title,
                    p.brand,
                    p.price,
                    p.rating,
                    p.reviews_count,
                    COUNT(r.review_id) as actual_reviews,
                    AVG(CAST(SUBSTR(r.rating, 1, 1) AS INTEGER)) as avg_rating,
                    COUNT(CASE WHEN r.is_verified = true THEN 1 END) as verified_reviews,
                    p.scraped_at
                FROM products p
                LEFT JOIN reviews r ON p.item_number = r.product_item_number
                GROUP BY p.item_number, p.title, p.brand, p.price, p.rating, p.reviews_count, p.scraped_at
            """
            return self.conn.execute(query).df()
    
    def get_reviews_by_rating(self, item_number: str, min_rating: int = 4) -> pd.DataFrame:
        """
        Get reviews filtered by minimum rating.
        
        Args:
            item_number: Product item number
            min_rating: Minimum rating (1-5)
        
        Returns:
            DataFrame with filtered reviews
        """
        query = """
            SELECT 
                review_id,
                title,
                rating,
                author,
                date,
                is_verified,
                pros,
                cons,
                overall_review,
                SUBSTR(full_content, 1, 200) as content_preview
            FROM reviews
            WHERE product_item_number = ? 
            AND CAST(SUBSTR(rating, 1, 1) AS INTEGER) >= ?
            ORDER BY CAST(SUBSTR(rating, 1, 1) AS INTEGER) DESC, date DESC
        """
        return self.conn.execute(query, [item_number, min_rating]).df()
    
    def get_rating_distribution(self, item_number: str) -> pd.DataFrame:
        """
        Get rating distribution for a product.
        
        Args:
            item_number: Product item number
        
        Returns:
            DataFrame with rating distribution
        """
        query = """
            SELECT 
                rating,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM reviews
            WHERE product_item_number = ?
            GROUP BY rating
            ORDER BY CAST(SUBSTR(rating, 1, 1) AS INTEGER) DESC
        """
        return self.conn.execute(query, [item_number]).df()
    
    def search_reviews(self, item_number: str, search_term: str) -> pd.DataFrame:
        """
        Search reviews for specific terms.
        
        Args:
            item_number: Product item number
            search_term: Term to search for
        
        Returns:
            DataFrame with matching reviews
        """
        query = """
            SELECT 
                review_id,
                title,
                rating,
                author,
                date,
                is_verified,
                pros,
                cons,
                overall_review,
                SUBSTR(full_content, 1, 300) as content_preview
            FROM reviews
            WHERE product_item_number = ?
            AND (
                LOWER(title) LIKE LOWER(?) OR
                LOWER(pros) LIKE LOWER(?) OR
                LOWER(cons) LIKE LOWER(?) OR
                LOWER(overall_review) LIKE LOWER(?) OR
                LOWER(full_content) LIKE LOWER(?)
            )
            ORDER BY date DESC
        """
        search_pattern = f"%{search_term}%"
        return self.conn.execute(query, [item_number, search_pattern, search_pattern, 
                                       search_pattern, search_pattern, search_pattern]).df()
    
    def get_recent_reviews(self, item_number: str, limit: int = 10) -> pd.DataFrame:
        """
        Get most recent reviews for a product.
        
        Args:
            item_number: Product item number
            limit: Number of reviews to return
        
        Returns:
            DataFrame with recent reviews
        """
        query = """
            SELECT 
                review_id,
                title,
                rating,
                author,
                date,
                is_verified,
                SUBSTR(full_content, 1, 200) as content_preview
            FROM reviews
            WHERE product_item_number = ?
            ORDER BY date DESC
            LIMIT ?
        """
        return self.conn.execute(query, [item_number, limit]).df()
    
    def export_to_csv(self, item_number: str, output_dir: str = "."):
        """
        Export product data to CSV files.
        
        Args:
            item_number: Product item number
            output_dir: Output directory for CSV files
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Export product summary
        summary_df = self.get_product_summary(item_number)
        if not summary_df.empty:
            summary_df.to_csv(f"{output_dir}/product_summary_{item_number}_{timestamp}.csv", index=False)
        
        # Export all reviews
        reviews_query = """
            SELECT * FROM reviews WHERE product_item_number = ?
        """
        reviews_df = self.conn.execute(reviews_query, [item_number]).df()
        if not reviews_df.empty:
            reviews_df.to_csv(f"{output_dir}/reviews_{item_number}_{timestamp}.csv", index=False)
        
        # Export rating distribution
        rating_df = self.get_rating_distribution(item_number)
        if not rating_df.empty:
            rating_df.to_csv(f"{output_dir}/rating_distribution_{item_number}_{timestamp}.csv", index=False)
        
        print(f"✅ Exported data to {output_dir}/")
    
    def close(self):
        """Close the DuckDB connection."""
        self.conn.close()

def example_usage():
    """Example of how to use the DuckDB integration."""
    
    # Load scraped data (assuming you have a JSON file)
    try:
        with open("scraped_data.json", "r") as f:
            scraped_data = json.load(f)
    except FileNotFoundError:
        print("❌ No scraped_data.json found. Please run the scraper first.")
        return
    
    # Initialize DuckDB
    db = NeweggDuckDB("newegg_data.duckdb")
    
    try:
        # Insert the scraped data
        db.insert_scraped_data(scraped_data)
        
        # Get product summary
        item_number = scraped_data["product"]["item_number"]
        print("\n📊 PRODUCT SUMMARY")
        print("=" * 50)
        summary = db.get_product_summary(item_number)
        print(summary.to_string(index=False))
        
        # Get rating distribution
        print("\n⭐ RATING DISTRIBUTION")
        print("=" * 50)
        ratings = db.get_rating_distribution(item_number)
        print(ratings.to_string(index=False))
        
        # Get high-rated reviews
        print("\n🔥 HIGH-RATED REVIEWS (4+ stars)")
        print("=" * 50)
        high_rated = db.get_reviews_by_rating(item_number, min_rating=4)
        print(high_rated[['title', 'rating', 'author', 'date']].to_string(index=False))
        
        # Search for specific terms
        print("\n🔍 SEARCHING FOR 'performance'")
        print("=" * 50)
        search_results = db.search_reviews(item_number, "performance")
        if not search_results.empty:
            print(search_results[['title', 'rating', 'author']].to_string(index=False))
        else:
            print("No reviews found containing 'performance'")
        
        # Export to CSV
        db.export_to_csv(item_number)
        
    finally:
        db.close()

if __name__ == "__main__":
    example_usage() 