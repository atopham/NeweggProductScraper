import time
import random
import asyncio
from typing import Dict, Optional, Callable
from dataclasses import dataclass
from collections import deque
import threading
from datetime import datetime, timedelta

@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_second: float = 1.0
    burst_size: int = 5
    min_delay: float = 0.5
    max_delay: float = 5.0
    adaptive: bool = True
    error_threshold: float = 0.1  # 10% error rate triggers backoff
    success_threshold: float = 0.9  # 90% success rate allows speedup

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter with adaptive behavior.
    Implements exponential backoff on errors and adaptive speedup on success.
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.tokens = config.burst_size
        self.last_refill = time.time()
        self.refill_rate = config.requests_per_second
        
        # Adaptive rate limiting
        self.current_rate = config.requests_per_second
        self.error_count = 0
        self.success_count = 0
        self.response_times = deque(maxlen=100)
        self.error_times = deque(maxlen=100)
        
        # Thread safety
        self.lock = threading.Lock()
    
    def _refill_tokens(self):
        """Refill tokens based on time elapsed."""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        
        self.tokens = min(self.config.burst_size, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def _adaptive_adjustment(self, success: bool, response_time: float):
        """Adjust rate based on success/failure and response time."""
        now = time.time()
        
        if success:
            self.success_count += 1
            self.response_times.append((now, response_time))
            
            # Calculate success rate
            total_requests = self.success_count + self.error_count
            if total_requests >= 10:
                success_rate = self.success_count / total_requests
                
                if success_rate > self.config.success_threshold:
                    # Speed up if consistently successful
                    self.current_rate = min(
                        self.current_rate * 1.1,
                        self.config.requests_per_second * 2.0
                    )
                    self.refill_rate = self.current_rate
        else:
            self.error_count += 1
            self.error_times.append(now)
            
            # Calculate error rate
            total_requests = self.success_count + self.error_count
            if total_requests >= 10:
                error_rate = self.error_count / total_requests
                
                if error_rate > self.config.error_threshold:
                    # Slow down on errors
                    self.current_rate = max(
                        self.current_rate * 0.5,
                        self.config.requests_per_second * 0.1
                    )
                    self.refill_rate = self.current_rate
    
    def acquire(self, timeout: Optional[float] = None) -> bool:
        """
        Acquire a token for making a request.
        
        Args:
            timeout: Maximum time to wait for a token
            
        Returns:
            True if token acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                self._refill_tokens()
                
                if self.tokens >= 1:
                    self.tokens -= 1
                    return True
                
                if timeout and (time.time() - start_time) > timeout:
                    return False
            
            # Wait before trying again
            time.sleep(0.1)
    
    def record_request(self, success: bool, response_time: float):
        """Record the result of a request for adaptive rate limiting."""
        if self.config.adaptive:
            self._adaptive_adjustment(success, response_time)
    
    def get_stats(self) -> Dict:
        """Get current rate limiter statistics."""
        total_requests = self.success_count + self.error_count
        success_rate = self.success_count / total_requests if total_requests > 0 else 0
        error_rate = self.error_count / total_requests if total_requests > 0 else 0
        
        avg_response_time = 0
        if self.response_times:
            avg_response_time = sum(time for _, time in self.response_times) / len(self.response_times)
        
        return {
            'current_rate': self.current_rate,
            'tokens_available': self.tokens,
            'total_requests': total_requests,
            'success_rate': success_rate,
            'error_rate': error_rate,
            'avg_response_time': avg_response_time
        }

class ConcurrentScraper:
    """
    Concurrent scraper with rate limiting and connection pooling.
    Manages multiple scrapers with proper resource management.
    """
    
    def __init__(self, max_workers: int = 3, rate_limit_config: Optional[RateLimitConfig] = None):
        """
        Initialize concurrent scraper.
        
        Args:
            max_workers: Maximum number of concurrent scrapers
            rate_limit_config: Rate limiting configuration
        """
        self.max_workers = max_workers
        self.rate_limiter = TokenBucketRateLimiter(rate_limit_config or RateLimitConfig())
        self.semaphore = asyncio.Semaphore(max_workers)
        self.active_tasks = set()
        self.results = []
        self.errors = []
    
    async def scrape_products(self, urls: list, scraper_factory: Callable, **kwargs):
        """
        Scrape multiple products concurrently.
        
        Args:
            urls: List of product URLs to scrape
            scraper_factory: Function that creates a scraper instance
            **kwargs: Additional arguments for the scraper
        
        Returns:
            List of scraping results
        """
        tasks = []
        
        for url in urls:
            task = asyncio.create_task(
                self._scrape_single_product(url, scraper_factory, **kwargs)
            )
            tasks.append(task)
            self.active_tasks.add(task)
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.errors.append({
                    'url': urls[i],
                    'error': str(result),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                self.results.append(result)
        
        return self.results
    
    async def _scrape_single_product(self, url: str, scraper_factory: Callable, **kwargs):
        """Scrape a single product with rate limiting."""
        async with self.semaphore:
            # Wait for rate limiter
            while not self.rate_limiter.acquire(timeout=1.0):
                await asyncio.sleep(0.1)
            
            start_time = time.time()
            success = False
            
            try:
                # Create scraper and scrape
                scraper = scraper_factory(**kwargs)
                result = await self._run_scraper(scraper, url)
                success = True
                return result
                
            except Exception as e:
                success = False
                raise e
            finally:
                response_time = time.time() - start_time
                self.rate_limiter.record_request(success, response_time)
    
    async def _run_scraper(self, scraper, url: str):
        """Run the scraper in a thread pool to avoid blocking."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, scraper.scrape_product, url)
    
    def get_stats(self) -> Dict:
        """Get scraping statistics."""
        return {
            'total_results': len(self.results),
            'total_errors': len(self.errors),
            'active_tasks': len(self.active_tasks),
            'rate_limiter_stats': self.rate_limiter.get_stats()
        }

class AdaptiveDelay:
    """
    Adaptive delay mechanism that adjusts based on website response patterns.
    """
    
    def __init__(self, base_delay: float = 1.0, max_delay: float = 10.0):
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.current_delay = base_delay
        self.response_times = deque(maxlen=50)
        self.error_count = 0
        self.success_count = 0
    
    def calculate_delay(self, last_response_time: Optional[float] = None, 
                       had_error: bool = False) -> float:
        """
        Calculate delay based on recent performance.
        
        Args:
            last_response_time: Time taken for last request
            had_error: Whether the last request failed
        
        Returns:
            Delay in seconds
        """
        if had_error:
            self.error_count += 1
            # Exponential backoff on errors
            self.current_delay = min(self.current_delay * 1.5, self.max_delay)
        else:
            self.success_count += 1
            if last_response_time:
                self.response_times.append(last_response_time)
            
            # Adjust based on response times
            if len(self.response_times) >= 10:
                avg_response_time = sum(self.response_times) / len(self.response_times)
                
                if avg_response_time < 1.0:  # Fast responses
                    self.current_delay = max(self.current_delay * 0.9, self.base_delay * 0.5)
                elif avg_response_time > 5.0:  # Slow responses
                    self.current_delay = min(self.current_delay * 1.2, self.max_delay)
        
        # Add some randomness to avoid patterns
        jitter = random.uniform(0.8, 1.2)
        return self.current_delay * jitter
    
    def reset(self):
        """Reset adaptive delay to base values."""
        self.current_delay = self.base_delay
        self.response_times.clear()
        self.error_count = 0
        self.success_count = 0 