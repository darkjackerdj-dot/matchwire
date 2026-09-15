import feedparser
import hashlib
import sqlite3
from datetime import datetime, timezone


FEEDS = {
    "BBC Sport": "https://feeds.bbci.co.uk/sport/football/rss.xml"
}


def init_db():
    conn = sqlite3.connect("football.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            news_hash TEXT UNIQUE,
            source TEXT,
            title TEXT,
            link TEXT,
            published TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    return conn


def make_hash(title):
    normalized = " ".join(title.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()


def get_news():
    all_news = []

    for source, feed_url in FEEDS.items():

        feed = feedparser.parse(feed_url)

        print(f"\n📰 {source}")
        print(f"Found {len(feed.entries)} articles")

        for entry in feed.entries[:10]:

            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            published = entry.get("published", "")

            if not title or not link:
                continue

            news_hash = make_hash(title)

            all_news.append({
                "hash": news_hash,
                "source": source,
                "title": title,
                "link": link,
                "published": published
            })

    return all_news


def save_new_news(news_items):

    conn = init_db()
    new_items = []

    for item in news_items:

        try:
            conn.execute(
                """
                INSERT INTO news
                (news_hash, source, title, link, published, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item["hash"],
                    item["source"],
                    item["title"],
                    item["link"],
                    item["published"],
                    datetime.now(timezone.utc).isoformat()
                )
            )

            new_items.append(item)

        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()

    return new_items


if __name__ == "__main__":

    print("⚽ Matchwire News Collector")
    print("=" * 40)

    news = get_news()
    new_news = save_new_news(news)

    print(f"\n🆕 New articles: {len(new_news)}")

    for item in new_news:
        print("\n" + item["title"])
        print(item["link"])
