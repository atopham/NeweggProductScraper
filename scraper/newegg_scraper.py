from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random
import re
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json

class NeweggScraper:
    """
    Simplified Newegg scraper that extracts product information and reviews.
    Designed to be DuckDB-ready with clean data structures.
    """
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
    
    def __enter__(self):
        """Context manager entry for browser setup."""
        self._setup_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit for browser cleanup."""
        self._cleanup()
    
    def _setup_browser(self):
        """Initialize browser with anti-detection measures."""
        playwright = sync_playwright().start()
        
        self.browser = playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor',
                '--disable-extensions',
                '--disable-plugins',
                '--disable-images',
                '--disable-javascript',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding',
                '--disable-features=TranslateUI',
                '--disable-ipc-flooding-protection'
            ]
        )
        
        self.context = self.browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
                'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"'
            }
        )
        
        self.page = self.context.new_page()
        self._setup_request_interception()
    
    def _cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            self.browser.close()
    
    def _setup_request_interception(self):
        """Set up request interception for API calls."""
        def handle_request(route):
            request = route.request
            if 'api/ProductReview' in request.url:
                headers = {
                    **request.headers,
                    'Referer': self.page.url,
                    'Origin': 'https://www.newegg.com',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/plain, */*',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Sec-Ch-Ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"macOS"'
                }
                route.continue_(headers=headers)
            else:
                route.continue_()
        
        self.page.route("**/*", handle_request)
    
    def _human_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Add human-like delay."""
        time.sleep(random.uniform(min_seconds, max_seconds))
    
    def _scroll_down(self, pixels: int = 800):
        """Scroll down the page."""
        self.page.mouse.wheel(0, pixels)
        self._human_delay(1, 2)
    
    def scrape_product(self, url: str, max_review_pages: Optional[int] = None) -> Dict:
        """
        Scrape complete product information including reviews.
        
        Args:
            url: Newegg product URL
            max_review_pages: Maximum number of review pages to scrape (None for all available pages)
        
        Returns:
            Dictionary with product info and reviews, ready for DuckDB insertion
        """
        print(f"🔍 Scraping product: {url}")
        
        # Load the product page
        self.page.goto(url, timeout=60000)
        self._human_delay(2, 4)
        
        # Extract product information
        product_info = self._extract_product_info()
        
        # Extract reviews (None means scrape all available pages)
        reviews = self._scrape_reviews(max_pages=max_review_pages)
        
        # Prepare DuckDB-ready data structure
        result = {
            "metadata": {
                "product_url": url,
                "scraped_at": datetime.now().isoformat(),
                "total_review_pages": len(reviews) if reviews else 0,
                "total_reviews": sum(len(page_reviews) for page_reviews in reviews) if reviews else 0,
                "scraper_version": "2.0"
            },
            "product": product_info,
            "reviews": reviews
        }
        
        print(f"✅ Scraping complete: {result['metadata']['total_reviews']} reviews from {result['metadata']['total_review_pages']} pages")
        return result
    
    def _extract_product_info(self) -> Dict:
        """Extract product information from the current page."""
        print("📦 Extracting product information...")
        
        # Get page content
        html = self.page.content()
        soup = BeautifulSoup(html, "lxml")
        
        # Extract with multiple selector fallbacks
        product_info = {
            "title": self._extract_text(soup, [
                "h1.product-title",
                ".product-title",
                "h1",
                "[data-testid='product-title']"
            ], "Title not found"),
            
            "brand": self._extract_text(soup, [
                "div.product-breadcrumb a",
                ".breadcrumbs a[href*='AMD']",
                ".seller-store-link a",
                "a[href*='AMD/BrandStore']"
            ], "Brand not found"),
            
            "price": self._extract_text(soup, [
                "li.price-current strong",
                ".price-current strong",
                ".price-current",
                "span.price-current-label + strong"
            ], "Price not found"),
            
            "rating": self._extract_text(soup, [
                "i.rating",
                "span.rating",
                ".product-rating i.rating"
            ], "No rating"),
            
            "reviews_count": self._extract_text(soup, [
                "span.item-rating-num",
                ".product-rating span[title*='reviews']",
                ".product-reviews span"
            ], "0"),
            
            "description": self._extract_text(soup, [
                "div.product-bullets ul",
                ".product-bullets",
                "ul.product-bullets"
            ], "Description not found"),
            
            "item_number": self._extract_item_number(self.page.url)
        }
        
        print(f"✅ Product info extracted: {product_info['title']}")
        return product_info
    
    def _extract_text(self, soup: BeautifulSoup, selectors: List[str], default: str) -> str:
        """Extract text using multiple selector fallbacks."""
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and text != "$":
                    return text
        return default
    
    def _extract_item_number(self, url: str) -> str:
        """Extract item number from URL."""
        match = re.search(r'/p/([A-Z0-9]+)', url)
        return match.group(1) if match else "Unknown"
    
    def _scrape_reviews(self, max_pages: Optional[int] = None) -> List[List[Dict]]:
        """Scrape reviews from all available pages."""
        print("📝 Starting review extraction...")
        
        # Navigate to reviews section
        if not self._navigate_to_reviews():
            print("❌ Could not navigate to reviews section")
            return []
        
        all_reviews = []
        current_page = 1
        
        while True:
            print(f"📄 Scraping review page {current_page}...")
            
            # Extract reviews from current page
            page_reviews = self._extract_page_reviews(current_page)
            
            if page_reviews:
                all_reviews.append(page_reviews)
                print(f"✅ Extracted {len(page_reviews)} reviews from page {current_page}")
            else:
                print(f"⚠️ No reviews found on page {current_page}")
                break
            
            # Check if we should continue based on max_pages parameter
            if max_pages is not None and current_page >= max_pages:
                print(f"🛑 Reached maximum page limit ({max_pages})")
                break
            
            # Try to go to next page
            if not self._navigate_to_next_page():
                print("🏁 No more pages available")
                break
            
            current_page += 1
            self._human_delay(2, 5)
        
        return all_reviews
    
    def _navigate_to_reviews(self) -> bool:
        """Navigate to the reviews section of the product page."""
        print("🔍 Looking for Reviews tab...")
        
        # Scroll down to find reviews section
        self._scroll_down(800)
        
        # Try multiple selectors for the reviews tab
        selectors = [
            'a.tab-nav[data-nav-title="Reviews"]',
            'a[href*="reviews"]',
            'a[data-nav-title*="Review"]',
            '.tab-nav[data-nav-title*="Review"]'
        ]
        
        for selector in selectors:
            try:
                element = self.page.locator(selector).first
                if element.count() > 0:
                    element.scroll_into_view_if_needed()
                    self._human_delay(1, 2)
                    
                    if element.is_visible():
                        element.click()
                        print(f"✅ Clicked Reviews tab with selector: {selector}")
                        self._human_delay(1, 3)
                        
                        # Scroll down to load reviews
                        self._scroll_down(600)
                        return True
            except Exception as e:
                print(f"Failed with selector {selector}: {e}")
                continue
        
        print("❌ Could not find or click reviews tab")
        return False
    
    def _extract_page_reviews(self, page_number: int) -> List[Dict]:
        """Extract reviews from the current page."""
        # Wait for reviews to load
        try:
            self.page.wait_for_selector('div.comments-cell.has-side-left.is-active', timeout=15000)
        except Exception:
            print("⚠️ No review elements found on this page")
            return []
        
        # Extract reviews using Python instead of JavaScript
        reviews = []
        
        # Find all review elements
        review_elements = self.page.locator('div.comments-cell.has-side-left.is-active').all()
        
        for i, element in enumerate(review_elements):
            try:
                review_data = self._extract_single_review(element, i + 1, page_number)
                reviews.append(review_data)
            except Exception as e:
                print(f"Error extracting review {i + 1}: {e}")
                continue
        
        return reviews
    
    def _extract_single_review(self, element, review_index: int, page_number: int) -> Dict:
        """Extract data from a single review element."""
        # Extract title
        title_element = element.locator('.comments-title-content, .review-title, .comment-title, h3, h4, .title').first
        title = title_element.inner_text().strip() if title_element.count() > 0 else f"Review {review_index}"
        
        # Extract rating
        rating_element = element.locator('.rating').first
        rating = "N/A"
        if rating_element.count() > 0:
            rating_class = rating_element.get_attribute("class") or ""
            rating_match = re.search(r'rating-(\d+)', rating_class)
            rating = f"{rating_match.group(1)}/5" if rating_match else "N/A"
        
        # Extract content
        content_element = element.locator('.comments-content, .review-content, .comment-content, .review-text, .content, p').first
        content = content_element.inner_text().strip() if content_element.count() > 0 else "No content found"
        
        # Extract author
        author_element = element.locator('.comments-name, .review-author, .comment-author, .author, .user-name, .username').first
        author = author_element.inner_text().strip() if author_element.count() > 0 else "Anonymous"
        
        # Extract date
        date_element = element.locator('.comments-text').first
        date = "N/A"
        if date_element.count() > 0:
            date_text = date_element.inner_text().strip()
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', date_text)
            date = date_match.group(1) if date_match else "N/A"
        
        # Extract verification status
        verified_element = element.locator('.comments-verified-owner').first
        is_verified = verified_element.count() > 0
        
        # Extract ownership duration
        ownership = "N/A"
        if date_element.count() > 0:
            ownership_text = date_element.inner_text().strip()
            if "Ownership:" in ownership_text:
                ownership = ownership_text.split("Ownership:")[1].strip()
        
        # Parse pros, cons, and overall review from content
        pros, cons, overall_review = self._parse_review_sections(content)
        
        return {
            "review_id": f"page_{page_number}_review_{review_index}",
            "page_number": page_number,
            "review_index": review_index,
            "title": title,
            "rating": rating,
            "author": author,
            "date": date,
            "is_verified": is_verified,
            "ownership": ownership,
            "pros": pros,
            "cons": cons,
            "overall_review": overall_review,
            "full_content": content,
            "timestamp": datetime.now().isoformat()
        }
    
    def _parse_review_sections(self, content: str) -> Tuple[str, str, str]:
        """Parse pros, cons, and overall review from review content."""
        pros = ""
        cons = ""
        overall_review = ""
        
        if not content:
            return "Not specified", "Not specified", "Not specified"
        
        lines = content.split('\n')
        current_section = ""
        
        for line in lines:
            trimmed_line = line.strip()
            if trimmed_line.lower().startswith('pros:'):
                current_section = 'pros'
                pros = trimmed_line.replace('pros:', '').strip()
            elif trimmed_line.lower().startswith('cons:'):
                current_section = 'cons'
                cons = trimmed_line.replace('cons:', '').strip()
            elif trimmed_line.lower().startswith('overall review:') or trimmed_line.lower().startswith('overall:'):
                current_section = 'overall'
                overall_review = trimmed_line.replace('overall review:', '').replace('overall:', '').strip()
            elif trimmed_line and current_section:
                if current_section == 'pros':
                    pros += (pros + ' ' if pros else '') + trimmed_line
                elif current_section == 'cons':
                    cons += (cons + ' ' if cons else '') + trimmed_line
                elif current_section == 'overall':
                    overall_review += (overall_review + ' ' if overall_review else '') + trimmed_line
        
        return (
            pros or "Not specified",
            cons or "Not specified", 
            overall_review or "Not specified"
        )
    
    def _navigate_to_next_page(self) -> bool:
        """Navigate to the next page of reviews."""
        print("🔍 Looking for next page...")
        
        # Check for next button
        next_button = self.page.locator('.paginations-next:not(.is-disabled)').first
        if next_button.count() > 0:
            next_button.click()
            print("✅ Clicked next button")
            self._human_delay(2, 4)
            return True
        
        # Check for pagination numbers
        current_page_element = self.page.locator('.paginations li a.button.is-active').first
        if current_page_element.count() > 0:
            current_page_text = current_page_element.inner_text().strip()
            try:
                current_page = int(current_page_text)
                next_page = current_page + 1
                
                # Look for next page number
                pagination_items = self.page.locator('.paginations li a.button').all()
                for item in pagination_items:
                    page_text = item.inner_text().strip()
                    try:
                        page_num = int(page_text)
                        if page_num == next_page:
                            item.click()
                            print(f"✅ Clicked page {next_page}")
                            self._human_delay(2, 4)
                            return True
                    except ValueError:
                        continue
            except ValueError:
                print(f"Could not parse current page number: {current_page_text}")
                pass
        
        print("❌ No next page found")
        return False

def scrape_newegg_product(url: str, max_review_pages: Optional[int] = None, headless: bool = True) -> Dict:
    """
    Convenience function to scrape a Newegg product.
    
    Args:
        url: Newegg product URL
        max_review_pages: Maximum number of review pages to scrape (None for all available pages)
        headless: Whether to run browser in headless mode
    
    Returns:
        Dictionary with product info and reviews, ready for DuckDB insertion
    """
    with NeweggScraper(headless=headless) as scraper:
        return scraper.scrape_product(url, max_review_pages)

# Example usage and DuckDB preparation
def prepare_for_duckdb(scraped_data: Dict) -> Dict:
    """
    Prepare scraped data for DuckDB insertion.
    
    Args:
        scraped_data: Data from scrape_newegg_product
    
    Returns:
        Dictionary with flattened data structures ready for DuckDB
    """
    product = scraped_data["product"]
    reviews = scraped_data["reviews"]
    metadata = scraped_data["metadata"]
    
    # Flatten reviews for easier DuckDB insertion
    flattened_reviews = []
    for page_reviews in reviews:
        for review in page_reviews:
            # Add product info to each review for denormalized table
            flattened_review = {
                **review,
                "product_url": metadata["product_url"],
                "product_title": product["title"],
                "product_brand": product["brand"],
                "product_price": product["price"],
                "product_rating": product["rating"],
                "product_reviews_count": product["reviews_count"],
                "product_item_number": product["item_number"],
                "scraped_at": metadata["scraped_at"]
            }
            flattened_reviews.append(flattened_review)
    
    return {
        "product_table": [product],
        "reviews_table": flattened_reviews,
        "metadata_table": [metadata]
    }

if __name__ == "__main__":
    # Example usage
    url = "https://www.newegg.com/amd-ryzen-7-9000-series-ryzen-7-9800x3d-granite-ridge-zen-5-socket-am5-desktop-cpu-processor/p/N82E16819113877"
    
    print("🚀 Starting Newegg scraper...")
    result = scrape_newegg_product(url, max_review_pages=2, headless=False)
    
    # Prepare for DuckDB
    duckdb_data = prepare_for_duckdb(result)
    
    print(f"\n📊 Results:")
    print(f"Product: {result['product']['title']}")
    print(f"Total reviews: {result['metadata']['total_reviews']}")
    print(f"Review pages: {result['metadata']['total_review_pages']}")
    
    # Save to JSON for inspection
    with open("scraped_data.json", "w") as f:
        json.dump(result, f, indent=2)
    
    print("\n💾 Data saved to scraped_data.json")
    print("🦆 Data ready for DuckDB insertion!") 