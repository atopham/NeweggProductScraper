from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import random
import re
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
from config import Config
from user_agents import UserAgentRotator, BrowserProfile
from rate_limiter import TokenBucketRateLimiter, RateLimitConfig, AdaptiveDelay
import threading

class EnhancedNeweggScraper:
    """
    Enhanced Newegg scraper with user agent rotation, rate limiting, and concurrency support.
    """
    
    def __init__(self, headless: bool = False, 
                 user_agent_strategy: str = "random",
                 rate_limit_config: Optional[RateLimitConfig] = None):
        """
        Initialize enhanced scraper.
        
        Args:
            headless: Whether to run browser in headless mode
            user_agent_strategy: "random", "sequential", or "weighted"
            rate_limit_config: Rate limiting configuration
        """
        self.headless = headless
        self.user_agent_rotator = UserAgentRotator(user_agent_strategy)
        self.rate_limiter = TokenBucketRateLimiter(rate_limit_config or RateLimitConfig())
        self.adaptive_delay = AdaptiveDelay()
        
        self.browser = None
        self.context = None
        self.page = None
        self.current_profile = None
        
        # Thread safety
        self.lock = threading.Lock()
    
    def __enter__(self):
        """Context manager entry for browser setup."""
        self._setup_browser()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit for browser cleanup."""
        self._cleanup()
    
    def _setup_browser(self):
        """Initialize browser with anti-detection measures and user agent rotation."""
        playwright = sync_playwright().start()
        
        # Get a new browser profile
        self.current_profile = self.user_agent_rotator.get_next_profile()
        
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
                '--disable-ipc-flooding-protection',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--disable-background-networking',
                '--disable-default-apps',
                '--disable-sync',
                '--metrics-recording-only',
                '--no-first-run',
                '--safebrowsing-disable-auto-update',
                '--disable-client-side-phishing-detection',
                '--disable-component-update',
                '--disable-domain-reliability'
            ]
        )
        
        # Create context with rotated user agent and headers
        headers = self.user_agent_rotator.get_headers(self.current_profile)
        viewport = self.user_agent_rotator.get_viewport(self.current_profile)
        
        self.context = self.browser.new_context(
            user_agent=self.current_profile.user_agent,
            viewport=viewport,
            extra_http_headers=headers
        )
        
        self.page = self.context.new_page()
        self._setup_request_interception()
        
        print(f"🔄 Using browser profile: {self.current_profile.user_agent[:50]}...")
    
    def _cleanup(self):
        """Clean up browser resources."""
        if self.browser:
            self.browser.close()
    
    def _setup_request_interception(self):
        """Set up request interception with rotated headers."""
        def handle_request(route):
            request = route.request
            if 'api/ProductReview' in request.url:
                # Use current profile headers for API requests
                headers = {
                    **request.headers,
                    'Referer': self.page.url,
                    'Origin': 'https://www.newegg.com',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/plain, */*',
                    'Content-Type': 'application/json',
                    'User-Agent': self.current_profile.user_agent,
                    'Sec-Fetch-Dest': 'empty',
                    'Sec-Fetch-Mode': 'cors',
                    'Sec-Fetch-Site': 'same-origin',
                    'Accept-Language': self.current_profile.accept_language,
                    'Accept-Encoding': self.current_profile.accept_encoding,
                    'Connection': 'keep-alive',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Sec-Ch-Ua': self.current_profile.sec_ch_ua,
                    'Sec-Ch-Ua-Mobile': self.current_profile.sec_ch_ua_mobile,
                    'Sec-Ch-Ua-Platform': self.current_profile.sec_ch_ua_platform
                }
                route.continue_(headers=headers)
            else:
                route.continue_()
        
        self.page.route("**/*", handle_request)
    
    def _rate_limited_delay(self):
        """Apply rate limiting and adaptive delays."""
        # Wait for rate limiter token
        if not self.rate_limiter.acquire(timeout=5.0):
            print("⚠️ Rate limit exceeded, waiting...")
            time.sleep(2.0)
            return
        
        # Calculate adaptive delay
        delay = self.adaptive_delay.calculate_delay()
        time.sleep(delay)
    
    def _rotate_user_agent(self):
        """Rotate to a new user agent profile."""
        with self.lock:
            old_profile = self.current_profile
            self.current_profile = self.user_agent_rotator.get_next_profile()
            
            if old_profile != self.current_profile:
                print(f"🔄 Rotating user agent to: {self.current_profile.user_agent[:50]}...")
                
                # Update page headers
                headers = self.user_agent_rotator.get_headers(self.current_profile)
                self.page.set_extra_http_headers(headers)
    
    def scrape_product(self, url: str, max_review_pages: Optional[int] = None) -> Dict:
        """
        Scrape complete product information including reviews with enhanced features.
        
        Args:
            url: Newegg product URL
            max_review_pages: Maximum number of review pages to scrape
        
        Returns:
            Dictionary with product info and reviews, ready for DuckDB insertion
        """
        print(f"🔍 Scraping product: {url}")
        
        start_time = time.time()
        success = False
        
        try:
            # Apply rate limiting
            self._rate_limited_delay()
            
            # Load the product page
            self.page.goto(url, timeout=60000)
            
            # Rotate user agent periodically
            if random.random() < 0.3:  # 30% chance to rotate
                self._rotate_user_agent()
            
            # Extract product information
            product_info = self._extract_product_info()
            
            # Extract reviews
            reviews = self._scrape_reviews(max_pages=max_review_pages)
            
            # Prepare result
            result = {
                "metadata": {
                    "product_url": url,
                    "scraped_at": datetime.now().isoformat(),
                    "total_review_pages": len(reviews) if reviews else 0,
                    "total_reviews": sum(len(page_reviews) for page_reviews in reviews) if reviews else 0,
                    "scraper_version": "3.0",
                    "user_agent": self.current_profile.user_agent,
                    "browser_profile": f"{self.current_profile.sec_ch_ua_platform} - {self.current_profile.sec_ch_ua}"
                },
                "product": product_info,
                "reviews": reviews
            }
            
            success = True
            response_time = time.time() - start_time
            
            # Record success for adaptive rate limiting
            self.rate_limiter.record_request(True, response_time)
            self.adaptive_delay.calculate_delay(response_time, False)
            
            print(f"✅ Scraping complete: {result['metadata']['total_reviews']} reviews from {result['metadata']['total_review_pages']} pages")
            return result
            
        except Exception as e:
            success = False
            response_time = time.time() - start_time
            
            # Record failure for adaptive rate limiting
            self.rate_limiter.record_request(False, response_time)
            self.adaptive_delay.calculate_delay(response_time, True)
            
            print(f"❌ Scraping failed: {str(e)}")
            raise e
    
    def _extract_product_info(self) -> Dict:
        """Extract product information from the current page."""
        print("📦 Extracting product information...")
        
        html = self.page.content()
        soup = BeautifulSoup(html, "lxml")
        
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

            "product_url": self.page.url,
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
        
        if not self._navigate_to_reviews():
            print("❌ Could not navigate to reviews section")
            return []
        
        all_reviews = []
        current_page = 1
        
        while True:
            print(f"📄 Scraping review page {current_page}...")
            
            # Apply rate limiting between pages
            self._rate_limited_delay()
            
            page_reviews = self._extract_page_reviews(current_page)
            
            if page_reviews:
                all_reviews.append(page_reviews)
                print(f"✅ Extracted {len(page_reviews)} reviews from page {current_page}")
            else:
                print(f"⚠️ No reviews found on page {current_page}")
                break
            
            if max_pages is not None and current_page >= max_pages:
                print(f"🛑 Reached maximum page limit ({max_pages})")
                break
            
            if not self._navigate_to_next_page():
                print("🏁 No more pages available")
                break
            
            current_page += 1
        
        return all_reviews
    
    def _navigate_to_reviews(self) -> bool:
        """Navigate to the reviews section of the product page."""
        print("🔍 Looking for Reviews tab...")
        
        self._scroll_down(800)
        
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
                    self._rate_limited_delay()
                    
                    if element.is_visible():
                        element.click()
                        print(f"✅ Clicked Reviews tab with selector: {selector}")
                        self._rate_limited_delay()
                        
                        self._scroll_down(600)
                        return True
            except Exception as e:
                print(f"Failed with selector {selector}: {e}")
                continue
        
        print("❌ Could not find or click reviews tab")
        return False
    
    def _extract_page_reviews(self, page_number: int) -> List[Dict]:
        """Extract reviews from the current page."""
        try:
            self.page.wait_for_selector('div.comments-cell.has-side-left.is-active', timeout=15000)
        except Exception:
            print("⚠️ No review elements found on this page")
            return []
        
        reviews = []
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
        title_element = element.locator('.comments-title-content, .review-title, .comment-title, h3, h4, .title').first
        title = title_element.inner_text().strip() if title_element.count() > 0 else f"Review {review_index}"
        
        rating_element = element.locator('.rating').first
        rating = "N/A"
        if rating_element.count() > 0:
            rating_class = rating_element.get_attribute("class") or ""
            rating_match = re.search(r'rating-(\d+)', rating_class)
            rating = f"{rating_match.group(1)}/5" if rating_match else "N/A"
        
        content_element = element.locator('.comments-content, .review-content, .comment-content, .review-text, .content, p').first
        content = content_element.inner_text().strip() if content_element.count() > 0 else "No content found"
        
        author_element = element.locator('.comments-name, .review-author, .comment-author, .author, .user-name, .username').first
        author = author_element.inner_text().strip() if author_element.count() > 0 else "Anonymous"
        
        date_element = element.locator('.comments-text').first
        date = "N/A"
        if date_element.count() > 0:
            date_text = date_element.inner_text().strip()
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', date_text)
            date = date_match.group(1) if date_match else "N/A"
        
        verified_element = element.locator('.comments-verified-owner').first
        is_verified = verified_element.count() > 0
        
        ownership = "N/A"
        if date_element.count() > 0:
            ownership_text = date_element.inner_text().strip()
            if "Ownership:" in ownership_text:
                ownership = ownership_text.split("Ownership:")[1].strip()
        
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
        
        next_button = self.page.locator('.paginations-next:not(.is-disabled)').first
        if next_button.count() > 0:
            next_button.click()
            print("✅ Clicked next button")
            self._rate_limited_delay()
            return True
        
        current_page_element = self.page.locator('.paginations li a.button.is-active').first
        if current_page_element.count() > 0:
            current_page_text = current_page_element.inner_text().strip()
            try:
                current_page = int(current_page_text)
                next_page = current_page + 1
                
                pagination_items = self.page.locator('.paginations li a.button').all()
                for item in pagination_items:
                    page_text = item.inner_text().strip()
                    try:
                        page_num = int(page_text)
                        if page_num == next_page:
                            item.click()
                            print(f"✅ Clicked page {next_page}")
                            self._rate_limited_delay()
                            return True
                    except ValueError:
                        continue
            except ValueError:
                print(f"Could not parse current page number: {current_page_text}")
                pass
        
        print("❌ No next page found")
        return False
    
    def _scroll_down(self, pixels: int = 800):
        """Scroll down the page."""
        self.page.mouse.wheel(0, pixels)
        time.sleep(random.uniform(1, 2))
    
    def get_stats(self) -> Dict:
        """Get scraper statistics."""
        return {
            'user_agent_stats': self.user_agent_rotator.get_usage_stats(),
            'rate_limiter_stats': self.rate_limiter.get_stats(),
            'current_profile': self.current_profile.user_agent if self.current_profile else None
        }

def create_enhanced_scraper(headless: bool = False, **kwargs) -> EnhancedNeweggScraper:
    """Factory function to create enhanced scraper instances."""
    return EnhancedNeweggScraper(headless=headless, **kwargs)

def scrape_newegg_product_enhanced(url: str, max_review_pages: Optional[int] = None, 
                                  headless: bool = False, **kwargs) -> Dict:
    """
    Enhanced convenience function to scrape a Newegg product.
    
    Args:
        url: Newegg product URL
        max_review_pages: Maximum number of review pages to scrape
        headless: Whether to run browser in headless mode
        **kwargs: Additional arguments for EnhancedNeweggScraper
    
    Returns:
        Dictionary with product info and reviews, ready for DuckDB insertion
    """
    with EnhancedNeweggScraper(headless=headless, **kwargs) as scraper:
        return scraper.scrape_product(url, max_review_pages)

if __name__ == "__main__":
    """Main function to run the enhanced scraper directly."""
    print("🚀 ENHANCED NEWEGG SCRAPER")
    print("=" * 50)
    
    # Example product URL
    url = "https://www.newegg.com/amd-ryzen-7-9000-series-ryzen-7-9800x3d-granite-ridge-zen-5-socket-am5-desktop-cpu-processor/p/N82E16819113877"
    
    print(f"Scraping: {url}")
    print("=" * 50)
    
    try:
        # Scrape with enhanced features
        result = scrape_newegg_product_enhanced(
            url=url,
            max_review_pages=Config.get_max_review_pages(),  # Limit for demo
            headless=Config.HEADLESS,  # Show browser
            user_agent_strategy="weighted"
        )
        
        print(f"\n✅ SCRAPING COMPLETE!")
        print(f"📦 Product: {result['product']['title']}")
        print(f"⭐ Rating: {result['product']['rating']}")
        print(f"💰 Price: {result['product']['price']}")
        print(f"📝 Total Reviews: {result['metadata']['total_reviews']}")
        print(f"🔄 User Agent: {result['metadata']['user_agent'][:50]}...")
        
        # Save to JSON
        with open("enhanced_scrape_result.json", "w") as f:
            json.dump(result, f, indent=2)
        print("\n💾 Results saved to enhanced_scrape_result.json")
        
    except Exception as e:
        print(f"\n❌ Scraping failed: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Check that all dependencies are installed:")
        print("   pip install -r requirements.txt")
        print("   playwright install chromium")
        print("2. Ensure all required files are in the same directory")
        print("3. Check your internet connection") 