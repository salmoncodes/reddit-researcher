"""Generate reports from stored data."""

from reddit_scraper.storage import Storage


def generate_report(storage, days=7):
    """Generate a text report."""
    stats = storage.get_stats(days)

    print(f"\n{'=' * 60}")
    print(f"REDDIT SCRAPER REPORT - Last {days} days")
    print(f"{'=' * 60}\n")

    print(f"Total posts stored: {stats['total_posts']}\n")

    print("Top 10 Subreddits by Volume:")
    print("-" * 40)
    for subreddit, count in stats["top_subreddits"]:
        print(f"  r/{subreddit}: {count} posts")

    print(f"\nTop 10 Discovered Subreddits by Subscribers:")
    print("-" * 40)
    for name, subs in stats["top_by_subscribers"]:
        print(f"  r/{name}: {subs:,} subscribers")

    print(f"\nTop 10 Tags by Frequency:")
    print("-" * 40)
    for tag, count in stats["tag_frequency"]:
        print(f"  {tag}: {count}")

    print(f"\n{'=' * 60}\n")
