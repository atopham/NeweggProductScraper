import random
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class BrowserProfile:
    """Browser profile with user agent and associated headers."""
    user_agent: str
    accept_language: str
    accept_encoding: str
    sec_ch_ua: str
    sec_ch_ua_mobile: str
    sec_ch_ua_platform: str
    viewport_width: int
    viewport_height: int

class UserAgentRotator:
    """
    Rotates user agents and browser profiles to avoid detection.
    Implements realistic browser fingerprinting.
    """
    
    def __init__(self, rotation_strategy: str = "random"):
        """
        Initialize user agent rotator.
        
        Args:
            rotation_strategy: "random", "sequential", or "weighted"
        """
        self.rotation_strategy = rotation_strategy
        self.current_index = 0
        self.profiles = self._create_browser_profiles()
        self.usage_count = {i: 0 for i in range(len(self.profiles))}
    
    def _create_browser_profiles(self) -> List[BrowserProfile]:
        """Create realistic browser profiles."""
        return [
            # Chrome on macOS
            BrowserProfile(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                accept_language="en-US,en;q=0.9",
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"macOS"',
                viewport_width=1920,
                viewport_height=1080
            ),
            # Chrome on Windows
            BrowserProfile(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                accept_language="en-US,en;q=0.9",
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"Windows"',
                viewport_width=1920,
                viewport_height=1080
            ),
            # Firefox on macOS
            BrowserProfile(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0",
                accept_language="en-US,en;q=0.5",
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Firefox";v="119"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"macOS"',
                viewport_width=1440,
                viewport_height=900
            ),
            # Firefox on Windows
            BrowserProfile(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0",
                accept_language="en-US,en;q=0.5",
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Firefox";v="119"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"Windows"',
                viewport_width=1920,
                viewport_height=1080
            ),
            # Safari on macOS
            BrowserProfile(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                accept_language="en-US,en;q=0.9",
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Safari";v="17.1"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"macOS"',
                viewport_width=1440,
                viewport_height=900
            ),
            # Edge on Windows
            BrowserProfile(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.2623.0",
                accept_language="en-US,en;q=0.9",
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Microsoft Edge";v="138", "Chromium";v="138", "Not)A;Brand";v="8"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"Windows"',
                viewport_width=1920,
                viewport_height=1080
            ),
            # Chrome on Linux
            BrowserProfile(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                accept_language="en-US,en;q=0.9",
                accept_encoding="gzip, deflate, br",
                sec_ch_ua='"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
                sec_ch_ua_mobile="?0",
                sec_ch_ua_platform='"Linux"',
                viewport_width=1920,
                viewport_height=1080
            )
        ]
    
    def get_next_profile(self) -> BrowserProfile:
        """Get the next browser profile based on rotation strategy."""
        if self.rotation_strategy == "random":
            profile_index = random.randint(0, len(self.profiles) - 1)
        elif self.rotation_strategy == "sequential":
            profile_index = self.current_index
            self.current_index = (self.current_index + 1) % len(self.profiles)
        elif self.rotation_strategy == "weighted":
            # Weighted selection - prefer less used profiles
            min_usage = min(self.usage_count.values())
            candidates = [i for i, count in self.usage_count.items() if count == min_usage]
            profile_index = random.choice(candidates)
        else:
            profile_index = 0
        
        self.usage_count[profile_index] += 1
        return self.profiles[profile_index]
    
    def get_headers(self, profile: Optional[BrowserProfile] = None) -> Dict[str, str]:
        """Get HTTP headers for a browser profile."""
        if profile is None:
            profile = self.get_next_profile()
        
        return {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': profile.accept_language,
            'Accept-Encoding': profile.accept_encoding,
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': profile.sec_ch_ua,
            'Sec-Ch-Ua-Mobile': profile.sec_ch_ua_mobile,
            'Sec-Ch-Ua-Platform': profile.sec_ch_ua_platform
        }
    
    def get_viewport(self, profile: Optional[BrowserProfile] = None) -> Dict[str, int]:
        """Get viewport dimensions for a browser profile."""
        if profile is None:
            profile = self.get_next_profile()
        
        return {
            'width': profile.viewport_width,
            'height': profile.viewport_height
        }
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get usage statistics for each profile."""
        return {
            f"Profile {i}": count for i, count in self.usage_count.items()
        }
    
    def reset_usage_stats(self):
        """Reset usage statistics."""
        self.usage_count = {i: 0 for i in range(len(self.profiles))} 