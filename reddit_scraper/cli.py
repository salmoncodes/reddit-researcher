"""Command-line interface."""

import argparse
import sys
from pathlib import Path

from reddit_scraper.storage import Storage
from reddit_scraper.reddit_json import RedditClient
from reddit_scraper.tagging import run_tagging
from reddit_scraper.reporting import generate_report
from reddit_scraper.export import export_all


def cmd_fetch(args):
    """Fetch posts from a subreddit."""
    storage = Storage(args.db)
    client = RedditClient()

    print(f"Fetching r/{args.subreddit} ({args.sort}, limit={args.limit})...")

    posts = client.fetch_subreddit(
        args.subreddit, sort=args.sort, time=args.time, limit=args.limit
    )

    saved = 0
    for post in posts:
        if storage.save_post(post, source=f"fetch/{args.subreddit}"):
            saved += 1

    storage.save_run(
        run_type="fetch",
        subreddit=args.subreddit,
        sort=args.sort,
        time=args.time,
        limit_n=args.limit,
        notes=f"Saved {saved} new posts",
    )

    print(f"Saved {saved} new posts ({len(posts)} total fetched)")

    # Auto-tag new posts
    run_tagging(storage)

    client.close()


def cmd_search(args):
    """Search for posts."""
    storage = Storage(args.db)
    client = RedditClient()

    scope = f"in r/{args.subreddit}" if args.subreddit else "sitewide"
    print(f"Searching {scope} for '{args.query}' (limit={args.limit})...")

    posts = client.search(
        args.query,
        subreddit=args.subreddit,
        sort=args.sort,
        time=args.time,
        limit=args.limit,
    )

    saved = 0
    for post in posts:
        if storage.save_post(post, source=f"search/{args.query}"):
            saved += 1

    storage.save_run(
        run_type="search",
        subreddit=args.subreddit,
        query=args.query,
        sort=args.sort,
        time=args.time,
        limit_n=args.limit,
        notes=f"Saved {saved} new posts",
    )

    print(f"Saved {saved} new posts ({len(posts)} total fetched)")

    # Auto-tag new posts
    run_tagging(storage)

    client.close()


def cmd_discover(args):
    """Discover subreddits."""
    storage = Storage(args.db)
    client = RedditClient()

    discovered = []

    if args.from_search:
        # Mode B: Mine subreddits from search results
        print(
            f"Discovering from search: '{args.from_search}' (limit={args.limit}, top_n={args.top_n})..."
        )

        subreddits = client.discover_from_search(
            args.from_search, time=args.time, limit=args.limit, top_n=args.top_n
        )

        print(f"Found {len(subreddits)} subreddits in search results")

        for name in subreddits:
            about = client.get_subreddit_about(name)
            if about:
                # Apply filters
                subs = about.get("subscribers", 0) or 0
                is_nsfw = about.get("over18", False)

                if subs >= args.min_subs:
                    if args.exclude_nsfw and is_nsfw:
                        continue

                    storage.save_subreddit(name, about, source="mined_from_search")
                    discovered.append(name)
                    print(f"  r/{name}: {subs:,} subscribers")

        storage.save_run(
            run_type="discover",
            query=args.from_search,
            limit_n=args.limit,
            notes=f"Discovered {len(discovered)} subreddits from search",
        )

    else:
        # Mode A: Search subreddits directly
        print(f"Discovering subreddits for query: '{args.query}'...")

        results = client.search_subreddits(args.query, limit=args.limit)

        for sub in results:
            name = sub.get("display_name")
            if not name:
                continue

            # Get detailed about info
            about = client.get_subreddit_about(name)
            if not about:
                about = sub  # Fallback to search result data

            subs = about.get("subscribers", 0) or 0
            is_nsfw = about.get("over18", False)

            if subs >= args.min_subs:
                if args.exclude_nsfw and is_nsfw:
                    continue

                storage.save_subreddit(name, about, source="subreddits_search")
                discovered.append(name)
                print(f"  r/{name}: {subs:,} subscribers")

        storage.save_run(
            run_type="discover",
            query=args.query,
            limit_n=args.limit,
            notes=f"Discovered {len(discovered)} subreddits",
        )

    print(f"\nSaved {len(discovered)} subreddits to database")
    client.close()


def cmd_comments(args):
    """Fetch comments for a post."""
    storage = Storage(args.db)
    client = RedditClient()

    print(f"Fetching comments for post {args.post_id} (limit={args.limit})...")

    comments = client.fetch_comments(args.post_id, limit=args.limit)

    saved = 0
    for comment in comments:
        storage.save_comment(comment, args.post_id)
        saved += 1

    storage.save_run(
        run_type="comments",
        query=args.post_id,
        limit_n=args.limit,
        notes=f"Saved {saved} comments",
    )

    print(f"Saved {saved} comments")
    client.close()


def cmd_export(args):
    """Export data to CSV."""
    storage = Storage(args.db)
    export_all(storage, args.out)


def cmd_report(args):
    """Generate report."""
    storage = Storage(args.db)
    generate_report(storage, days=args.days)


def main():
    parser = argparse.ArgumentParser(
        description="Reddit Scraper - Market research for study-related content"
    )
    parser.add_argument(
        "--db",
        default=None,
        help="Database path (default: ./data/reddit_scraper.sqlite)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # fetch
    fetch_parser = subparsers.add_parser("fetch", help="Fetch posts from a subreddit")
    fetch_parser.add_argument("--subreddit", required=True, help="Subreddit name")
    fetch_parser.add_argument(
        "--sort", default="hot", choices=["hot", "new", "top", "rising"]
    )
    fetch_parser.add_argument(
        "--time", default=None, choices=["hour", "day", "week", "month", "year", "all"]
    )
    fetch_parser.add_argument("--limit", type=int, default=50, help="Number of posts")
    fetch_parser.set_defaults(func=cmd_fetch)

    # search
    search_parser = subparsers.add_parser("search", help="Search for posts")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--subreddit", default=None, help="Limit to subreddit")
    search_parser.add_argument(
        "--sort",
        default="relevance",
        choices=["relevance", "hot", "top", "new", "comments"],
    )
    search_parser.add_argument(
        "--time", default=None, choices=["hour", "day", "week", "month", "year", "all"]
    )
    search_parser.add_argument(
        "--limit", type=int, default=50, help="Number of results"
    )
    search_parser.set_defaults(func=cmd_search)

    # discover
    discover_parser = subparsers.add_parser("discover", help="Discover subreddits")
    discover_group = discover_parser.add_mutually_exclusive_group(required=True)
    discover_group.add_argument("--query", help="Search query for subreddits")
    discover_group.add_argument(
        "--from-search", dest="from_search", help="Mine subreddits from search results"
    )
    discover_parser.add_argument("--limit", type=int, default=50, help="Max results")
    discover_parser.add_argument(
        "--top-n",
        type=int,
        default=50,
        help="Top N subreddits from search (with --from-search)",
    )
    discover_parser.add_argument(
        "--time", default=None, choices=["hour", "day", "week", "month", "year", "all"]
    )
    discover_parser.add_argument(
        "--min-subs", type=int, default=1000, help="Minimum subscribers"
    )
    discover_parser.add_argument(
        "--exclude-nsfw",
        action="store_true",
        default=True,
        help="Exclude NSFW subreddits",
    )
    discover_parser.set_defaults(func=cmd_discover)

    # comments
    comments_parser = subparsers.add_parser(
        "comments", help="Fetch comments for a post"
    )
    comments_parser.add_argument("--post-id", required=True, help="Reddit post ID")
    comments_parser.add_argument(
        "--limit", type=int, default=50, help="Number of comments"
    )
    comments_parser.set_defaults(func=cmd_comments)

    # export
    export_parser = subparsers.add_parser("export", help="Export data to CSV")
    export_parser.add_argument("--out", default="./exports", help="Output directory")
    export_parser.set_defaults(func=cmd_export)

    # report
    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("--days", type=int, default=7, help="Days to report on")
    report_parser.set_defaults(func=cmd_report)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
