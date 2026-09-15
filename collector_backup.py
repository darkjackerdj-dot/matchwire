import feedparser
import re
from urllib.parse import urlparse

from filter import is_good_news, is_rumour


# ============================================================
# VERIFIED SOURCES
# ============================================================

SOURCES = {
    "BBC Sport": "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "ESPN": "https://www.espn.co.uk/espn/rss/football/news",
}


# ============================================================
# TRUSTED DOMAINS
# ============================================================

TRUSTED_DOMAINS = {
    "bbc.co.uk",
    "bbci.co.uk",
    "espn.com",
    "espn.co.uk",
}


# ============================================================
# IMPORTANT FOOTBALL ENTITIES
# ============================================================

ENTITIES = [

    # Clubs
    "arsenal",
    "chelsea",
    "liverpool",
    "manchester united",
    "manchester city",
    "tottenham",
    "newcastle",
    "aston villa",
    "real madrid",
    "barcelona",
    "bayern",
    "psg",
    "juventus",
    "inter milan",
    "ac milan",
    "santos",

    # Players
    "neymar",
    "messi",
    "mbappe",
    "haaland",
    "salah",
    "kane",
    "rodri",
    "coutinho",
    "richarlison",

    # Topics
    "var",
    "transfer",
    "injury",
    "squad",
    "manager",
    "referee",
]


# ============================================================
# TRUSTED LINK CHECK
# ============================================================

def is_trusted_link(link):

    try:

        hostname = urlparse(link).hostname

        if not hostname:
            return False

        hostname = hostname.lower()

        for domain in TRUSTED_DOMAINS:

            if hostname == domain:
                return True

            if hostname.endswith("." + domain):
                return True

        return False

    except Exception:

        return False


# ============================================================
# CLEAN TITLE
# ============================================================

def clean_title(title):

    title = title.lower()

    title = re.sub(
        r"\s*[-|]\s*(bbc sport|espn|espn fc)\s*$",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"[^a-z0-9\s]",
        " ",
        title
    )

    return " ".join(title.split())


# ============================================================
# GET ENTITIES FROM TITLE
# ============================================================

def get_entities(title):

    cleaned = clean_title(title)

    found = set()

    for entity in ENTITIES:

        if entity in cleaned:
            found.add(entity)

    return found


# ============================================================
# SAFE STORY MATCH
# ============================================================

def similar_story(title1, title2):

    clean1 = clean_title(title1)
    clean2 = clean_title(title2)

    words1 = set(clean1.split())
    words2 = set(clean2.split())

    if not words1 or not words2:
        return False

    # --------------------------------------------
    # Exact / very strong title similarity
    # --------------------------------------------

    common_words = words1.intersection(words2)

    similarity = len(common_words) / max(
        len(words1),
        len(words2)
    )

    if similarity >= 0.70:
        return True


    # --------------------------------------------
    # Entity-based similarity
    # --------------------------------------------

    entities1 = get_entities(title1)
    entities2 = get_entities(title2)

    common_entities = entities1.intersection(
        entities2
    )

    # Need at least TWO strong common entities.
    # This prevents unrelated stories about the
    # same club/player from being merged.
    if len(common_entities) >= 2:

        return True


    return False


# ============================================================
# DUPLICATE / STORY GROUPING
# ============================================================

def remove_duplicates(articles):

    unique_articles = []

    for article in articles:

        duplicate = False

        for existing in unique_articles:

            if similar_story(
                article["title"],
                existing["title"]
            ):

                existing["sources"].append(
                    article["source"]
                )

                duplicate = True

                break


        if not duplicate:

            article["sources"] = [
                article["source"]
            ]

            unique_articles.append(article)


    return unique_articles


# ============================================================
# COLLECT NEWS
# ============================================================

def collect_news():

    all_articles = []

    print("\n===================================")
    print("      MATCHWIRE NEWS COLLECTOR")
    print("===================================")


    for source, feed_url in SOURCES.items():

        print(f"\n📰 Checking {source}...")


        try:

            feed = feedparser.parse(
                feed_url
            )

            print(
                f"📥 Found {len(feed.entries)} articles"
            )

        except Exception as error:

            print(
                f"❌ Failed to read {source}: {error}"
            )

            continue


        for entry in feed.entries[:20]:

            title = entry.get(
                "title",
                ""
            ).strip()

            link = entry.get(
                "link",
                ""
            ).strip()

            published = entry.get(
                "published",
                ""
            ).strip()


            # ----------------------------------------
            # BASIC CHECK
            # ----------------------------------------

            if not title or not link:
                continue


            # ----------------------------------------
            # TRUSTED SOURCE
            # ----------------------------------------

            if not is_trusted_link(link):

                continue


            # ----------------------------------------
            # QUALITY FILTER
            # ----------------------------------------

            if not is_good_news(title):

                continue


            # ----------------------------------------
            # RUMOUR CHECK
            # ----------------------------------------

            rumour = is_rumour(title)


            all_articles.append({

                "source": source,

                "title": title,

                "link": link,

                "published": published,

                "rumour": rumour,

            })


    print("\n===================================")

    print(
        f"📊 Articles after filtering: "
        f"{len(all_articles)}"
    )


    # --------------------------------------------
    # STORY GROUPING / DUPLICATE REMOVAL
    # --------------------------------------------

    unique_articles = remove_duplicates(
        all_articles
    )


    print(
        f"✅ Articles after story grouping: "
        f"{len(unique_articles)}"
    )


    print("===================================\n")


    return unique_articles


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    articles = collect_news()


    for index, article in enumerate(
        articles,
        start=1
    ):

        print(
            f"\n{index}. {article['title']}"
        )

        print(
            f"   Source: {article['source']}"
        )

        print(
            f"   Sources: "
            f"{', '.join(article['sources'])}"
        )

        print(
            f"   Rumour: "
            f"{'YES ⚠️' if article['rumour'] else 'NO ✅'}"
        )

        print(
            f"   Link: {article['link']}"
        )
