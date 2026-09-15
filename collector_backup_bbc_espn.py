import feedparser
import re
from urllib.parse import urlparse

from filter import is_good_news, is_rumour


# ============================================================
# NEWS SOURCES
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
# IMPORTANT NEWS KEYWORDS
# ============================================================

HIGH_IMPORTANCE = [
    "breaking",
    "confirmed",
    "official",
    "signed",
    "signs",
    "signing",
    "joins",
    "joined",
    "leaves",
    "left",
    "appointed",
    "sacked",
    "dismissed",
    "resigned",
    "retires",
    "retired",
    "injury",
    "injured",
    "surgery",
    "suspended",
    "suspension",
    "ban",
    "banned",
    "selected",
    "selection",
    "squad",
    "final",
    "winner",
    "wins",
    "won",
    "defeat",
    "lost",
    "draw",
    "drawn",
    "penalty",
    "red card",
    "var error",
    "referee error",
]


MEDIUM_IMPORTANCE = [
    "transfer",
    "transfers",
    "contract",
    "deal",
    "agreed",
    "agreement",
    "negotiations",
    "manager",
    "coach",
    "captain",
    "goal",
    "goals",
    "match",
    "champions league",
    "premier league",
    "europa league",
    "conference league",
    "world cup",
    "club world cup",
    "fa cup",
    "carabao cup",
]


# ============================================================
# MAJOR FOOTBALL ENTITIES
# ============================================================

ENTITIES = [
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
    "atletico madrid",
    "bayern",
    "borussia dortmund",
    "psg",
    "juventus",
    "inter milan",
    "ac milan",
    "santos",

    "neymar",
    "messi",
    "ronaldo",
    "mbappe",
    "haaland",
    "salah",
    "kane",
    "rodri",
    "coutinho",
    "richarlison",
]


# ============================================================
# TITLE CLEANING
# ============================================================

def clean_title(title):

    title = title.lower()

    title = re.sub(
        r"\s*[-|]\s*(bbc sport|espn|espn fc|fotmob|sofascore)\s*$",
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
# ENTITY DETECTION
# ============================================================

def get_entities(title):

    cleaned = clean_title(title)

    found = set()

    for entity in ENTITIES:

        if entity in cleaned:
            found.add(entity)

    return found


# ============================================================
# NEWS IMPORTANCE SCORE
# ============================================================

def importance_score(title):

    cleaned = clean_title(title)

    score = 0

    # High importance words
    for word in HIGH_IMPORTANCE:

        if word in cleaned:
            score += 2


    # Medium importance words
    for word in MEDIUM_IMPORTANCE:

        if word in cleaned:
            score += 1


    # Major player/team mentioned
    entities = get_entities(title)

    if len(entities) >= 1:
        score += 1

    if len(entities) >= 2:
        score += 1


    # Transfer rumours get lower priority
    if is_rumour(title):
        score -= 1


    return score


# ============================================================
# IMPORTANT NEWS CHECK
# ============================================================

def is_important_news(title):

    score = importance_score(title)

    # Minimum score for automatic Telegram delivery
    return score >= 2


# ============================================================
# STORY SIMILARITY
# ============================================================

def similar_story(title1, title2):

    clean1 = clean_title(title1)
    clean2 = clean_title(title2)

    words1 = set(clean1.split())
    words2 = set(clean2.split())

    if not words1 or not words2:
        return False

    common_words = words1.intersection(words2)

    similarity = (
        len(common_words)
        / max(len(words1), len(words2))
    )

    if similarity >= 0.70:
        return True


    entities1 = get_entities(title1)
    entities2 = get_entities(title2)

    common_entities = (
        entities1.intersection(entities2)
    )

    if len(common_entities) >= 2:
        return True


    return False


# ============================================================
# REMOVE DUPLICATES / GROUP STORIES
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

                # Keep highest priority score
                if article["score"] > existing["score"]:

                    existing["score"] = article["score"]

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

    print("")
    print("===================================")
    print("      MATCHWIRE NEWS COLLECTOR")
    print("===================================")


    # --------------------------------------------------------
    # READ EACH SOURCE
    # --------------------------------------------------------

    for source, feed_url in SOURCES.items():

        print("")
        print(f"📰 Checking {source}...")

        try:

            feed = feedparser.parse(
                feed_url
            )

            print(
                f"📥 Found {len(feed.entries)} articles"
            )

        except Exception as error:

            print(
                f"❌ Failed to read "
                f"{source}: {error}"
            )

            continue


        # ----------------------------------------------------
        # PROCESS ARTICLES
        # ----------------------------------------------------

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


            if not title or not link:
                continue


            # Trusted website only
            if not is_trusted_link(link):
                continue


            # Basic football-quality filter
            if not is_good_news(title):
                continue


            # Importance score
            score = importance_score(title)


            # Important news only
            if not is_important_news(title):
                continue


            rumour = is_rumour(title)


            all_articles.append({
                "source": source,
                "title": title,
                "link": link,
                "published": published,
                "rumour": rumour,
                "score": score,
            })


    # --------------------------------------------------------
    # SORT BY IMPORTANCE
    # --------------------------------------------------------

    all_articles.sort(
        key=lambda article: article["score"],
        reverse=True
    )


    print("")
    print("===================================")
    print(
        f"📊 Important articles: "
        f"{len(all_articles)}"
    )


    # --------------------------------------------------------
    # GROUP DUPLICATE STORIES
    # --------------------------------------------------------

    unique_articles = remove_duplicates(
        all_articles
    )


    print(
        f"✅ Unique important stories: "
        f"{len(unique_articles)}"
    )

    print("===================================")
    print("")


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
            f"{index}. "
            f"[Score {article['score']}] "
            f"{article['title']}"
        )

        print(
            f"   Source: "
            f"{article['source']}"
        )

        print(
            f"   Rumour: "
            f"{'YES ⚠️' if article['rumour'] else 'NO ✅'}"
        )

        print(
            f"   Link: "
            f"{article['link']}"
        )

        print("-----------------------------------")
