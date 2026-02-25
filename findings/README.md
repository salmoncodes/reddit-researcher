# Reddit Scraper

Fetches Reddit posts via public JSON API, stores in SQLite.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# Fetch posts
python -m reddit_scraper fetch --subreddit studying --limit 50

# Search
python -m reddit_scraper search --query "note taking" --subreddit studying --limit 50

# Discover subreddits
python -m reddit_scraper discover --query "study tips" --limit 25

# Get comments
python -m reddit_scraper comments --post-id abc123 --limit 50

# Generate report
python -m reddit_scraper report --days 7

# Export to CSV
python -m reddit_scraper export --out ./exports
```

## Database

SQLite file: `./data/reddit_scraper.db`

Tables: `posts`, `runs`, `subreddits`, `comments`, `post_tags`

Query it directly:
```bash
sqlite3 data/reddit_scraper.db "SELECT * FROM posts LIMIT 5;"
```

## Rate Limits

- 1 second between requests
- Exponential backoff on errors
- Be respectful, don't hammer Reddit

## Files NOT to commit

- `data/` - Database
- `exports/` - CSV files
- `venv/` - Virtual environment
- `__pycache__/` - Python cache
