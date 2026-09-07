#!/usr/bin/env python3
"""Count stock ticker mentions in a few finance subreddits (read-only).

Runs twice a day from a scheduled job. Reads the newest posts and top-level
comments, extracts ticker symbols with a regular expression, and stores only
per-ticker daily counts in a local SQLite table. No post text, usernames or
comment bodies are stored. The script never writes anything to Reddit.
"""
import os
import re
import sqlite3
import time
from datetime import date

import praw

SUBREDDITS = ["stocks", "investing", "wallstreetbets", "options", "StockMarket"]
POSTS_PER_SUBREDDIT = 100          # one listing request per subreddit
COMMENTS_PER_POST = 20             # top-level only, no "load more" expansion
TICKER = re.compile(r"(?<![A-Za-z])\$?([A-Z]{2,5})(?![A-Za-z])")
STOPWORDS = {"CEO", "IPO", "ETF", "USD", "YOLO", "DD", "FOMO", "ATH", "EPS", "GDP", "FED", "SEC", "AI", "US", "UK", "EU"}
DB = os.environ.get("TICKER_DB", "ticker_mentions.sqlite")


def reddit():
    return praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ.get("REDDIT_USER_AGENT", "ticker-mentions/1.0 (read-only; by u/KeyWinner4034)"),
        ratelimit_seconds=60,
    )


def tickers(text):
    return {t for t in TICKER.findall(text or "") if t not in STOPWORDS}


def main():
    api = reddit()
    today = date.today().isoformat()
    counts = {}
    for name in SUBREDDITS:
        for post in api.subreddit(name).new(limit=POSTS_PER_SUBREDDIT):
            seen = tickers(post.title) | tickers(post.selftext)
            post.comments.replace_more(limit=0)          # never expand "more comments"
            for comment in post.comments[:COMMENTS_PER_POST]:
                seen |= tickers(getattr(comment, "body", ""))
            for t in seen:
                counts[t] = counts.get(t, 0) + 1
            # text is discarded here; only the counter above survives
        time.sleep(2)                                    # stay far below 100 requests/minute
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS mentions (day TEXT, ticker TEXT, mentions INTEGER, PRIMARY KEY(day, ticker))")
    con.executemany("INSERT OR REPLACE INTO mentions VALUES (?, ?, ?)", [(today, t, n) for t, n in counts.items()])
    con.commit()
    con.close()
    print(f"{today}: {len(counts)} tickers counted")


if __name__ == "__main__":
    main()
