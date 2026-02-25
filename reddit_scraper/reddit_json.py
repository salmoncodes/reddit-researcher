"""Reddit JSON API client."""

from collections import Counter
from reddit_scraper.util import RedditSession


class RedditClient:
    """Client for Reddit's public JSON API."""

    BASE_URL = "https://www.reddit.com"

    def __init__(self):
        self.session = RedditSession()

    def fetch_subreddit(self, subreddit, sort="hot", time=None, limit=25):
        """Fetch posts from a subreddit."""
        url = f"{self.BASE_URL}/r/{subreddit}/{sort}.json"
        params = {"limit": limit}
        if time:
            params["t"] = time

        data = self.session.get(url, params)
        if not data or "data" not in data:
            return []

        return [child["data"] for child in data["data"].get("children", [])]

    def search(self, query, subreddit=None, sort="relevance", time=None, limit=25):
        """Search for posts."""
        if subreddit:
            url = f"{self.BASE_URL}/r/{subreddit}/search.json"
            params = {"q": query, "restrict_sr": "1", "limit": limit, "sort": sort}
        else:
            url = f"{self.BASE_URL}/search.json"
            params = {"q": query, "limit": limit, "sort": sort}

        if time:
            params["t"] = time

        data = self.session.get(url, params)
        if not data or "data" not in data:
            return []

        return [child["data"] for child in data["data"].get("children", [])]

    def search_subreddits(self, query, limit=25):
        """Search for subreddits by name/topic."""
        url = f"{self.BASE_URL}/subreddits/search.json"
        params = {"q": query, "limit": limit}

        data = self.session.get(url, params)
        if not data or "data" not in data:
            return []

        return [child["data"] for child in data["data"].get("children", [])]

    def get_subreddit_about(self, subreddit):
        """Get subreddit metadata."""
        url = f"{self.BASE_URL}/r/{subreddit}/about.json"
        data = self.session.get(url)

        if data and "data" in data:
            return data["data"]
        return None

    def fetch_comments(self, post_id, sort="top", limit=25):
        """Fetch comments for a post."""
        url = f"{self.BASE_URL}/comments/{post_id}.json"
        params = {"limit": limit, "sort": sort}

        data = self.session.get(url, params)
        if not data or len(data) < 2:
            return []

        # Comments are in the second element
        comments = []
        for child in data[1]["data"].get("children", []):
            if child.get("kind") == "t1":  # Comment
                comments.append(child["data"])

        return comments

    def discover_from_search(self, query, time=None, limit=200, top_n=50):
        """Discover subreddits by analyzing search results."""
        posts = self.search(query, time=time, limit=limit)

        # Count subreddit frequency
        subreddit_counts = Counter(post["subreddit"] for post in posts)
        top_subreddits = subreddit_counts.most_common(top_n)

        return [name for name, count in top_subreddits]

    def close(self):
        self.session.close()
