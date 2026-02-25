"""Utility functions for HTTP requests with rate limiting and backoff."""

import time
import random
from urllib.parse import urlencode

import requests


class RedditSession:
    """HTTP session with rate limiting and exponential backoff."""

    def __init__(self, base_delay=1.0):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
        )
        self.base_delay = base_delay
        self.last_request_time = 0

    def _rate_limit(self):
        """Enforce minimum delay between requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.base_delay:
            time.sleep(self.base_delay - elapsed)

    def get(self, url, params=None, max_retries=3):
        """GET with rate limiting and exponential backoff."""
        if params:
            url = f"{url}?{urlencode(params)}"

        for attempt in range(max_retries):
            self._rate_limit()

            try:
                response = self.session.get(url, timeout=30)
                self.last_request_time = time.time()

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    # Rate limited - exponential backoff
                    sleep_time = (2**attempt) + random.uniform(0, 1)
                    print(f"  Rate limited (429). Backing off {sleep_time:.1f}s...")
                    time.sleep(sleep_time)
                elif response.status_code >= 500:
                    # Server error - retry
                    sleep_time = (2**attempt) + random.uniform(0, 1)
                    print(
                        f"  Server error ({response.status_code}). Retrying in {sleep_time:.1f}s..."
                    )
                    time.sleep(sleep_time)
                else:
                    print(f"  HTTP {response.status_code} for {url}")
                    return None

            except requests.RequestException as e:
                print(f"  Request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2**attempt)

        return None

    def close(self):
        self.session.close()
