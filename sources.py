import feedparser


SOURCES = {
    "BBC Sport": "https://feeds.bbci.co.uk/sport/football/rss.xml",

    "ESPN": (
        "https://news.google.com/rss/search?"
        "q=site%3Aespn.com%2Fsoccer+football"
        "&hl=en-US&gl=US&ceid=US%3Aen"
    ),

    "FotMob": (
        "https://news.google.com/rss/search?"
        "q=site%3Afotmob.com+football"
        "&hl=en-US&gl=US&ceid=US%3Aen"
    ),

    "Sofascore": (
        "https://news.google.com/rss/search?"
        "q=site%3Asofascore.com%2Fnews+football"
        "&hl=en-US&gl=US&ceid=US%3Aen"
    ),
}


def get_articles():

    for source_name, feed_url in SOURCES.items():

        print("\n" + "=" * 50)
        print(f"📰 SOURCE: {source_name}")
        print("=" * 50)

        feed = feedparser.parse(feed_url)

        print(f"Articles found: {len(feed.entries)}")

        for article in feed.entries[:5]:

            title = article.get("title", "").strip()
            link = article.get("link", "").strip()

            if not title or not link:
                continue

            print(f"\n• {title}")
            print(f"  {link}")


if __name__ == "__main__":
    print("⚽ MATCHWIRE MULTI-SOURCE TEST")
    get_articles()
