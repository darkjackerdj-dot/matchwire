import re
import html
from urllib.parse import urlparse

import feedparser

from filter import is_good_news, is_rumour


# ============================================================
# MATCHWIRE NEWS SOURCES
# ============================================================

SOURCES = [
    {
        "name": "BBC Sport",
        "url": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "domains": ["bbc.co.uk", "bbci.co.uk"],
    },
    {
        "name": "ESPN",
        "url": "https://www.espn.co.uk/espn/rss/football/news",
        "domains": ["espn.com", "espn.co.uk"],
    },
    {
        "name": "The Guardian",
        "url": "https://feeds.theguardian.com/theguardian/football",
        "domains": ["theguardian.com"],
    },
]


# ============================================================
# IMPORTANCE WORDS
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
    "premier league",
    "champions league",
    "europa league",
    "conference league",
    "world cup",
    "fa cup",
    "league cup",
]


# ============================================================
# FOOTBALL ENTITIES
# ============================================================

FOOTBALL_ENTITIES = [
    # Premier League clubs
    "arsenal",
    "chelsea",
    "liverpool",
    "manchester united",
    "manchester city",
    "tottenham",
    "newcastle",
    "aston villa",
    "everton",
    "west ham",
    "brighton",
    "fulham",
    "crystal palace",
    "nottingham forest",
    "wolves",
    "bournemouth",
    "brentford",
    "ipswich",
    "leeds",
    "sunderland",

    # Major European clubs
    "real madrid",
    "barcelona",
    "atletico madrid",
    "bayern munich",
    "borussia dortmund",
    "psg",
    "paris saint-germain",
    "juventus",
    "inter milan",
    "ac milan",
    "napoli",
    "roma",

    # Competitions
    "premier league",
    "champions league",
    "europa league",
    "conference league",
    "world cup",
    "fa cup",
    "league cup",
    "la liga",
    "bundesliga",
    "serie a",
    "ligue 1",

    # Football terms
    "football",
    "soccer",
    "manager",
    "coach",
    "striker",
    "midfielder",
    "defender",
    "goalkeeper",
    "referee",
    "var",
]


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):
    if not text:
        return ""

    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def get_domain(url):
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def is_trusted_domain(url, trusted_domains):
    domain = get_domain(url)

    for trusted in trusted_domains:
        if domain == trusted or domain.endswith("." + trusted):
            return True

    return False


def importance_score(title):
    text = title.lower()

    score = 0

    for word in HIGH_IMPORTANCE:
        if word in text:
            score += 2

    for word in MEDIUM_IMPORTANCE:
        if word in text:
            score += 1

    entity_count = 0

    for entity in FOOTBALL_ENTITIES:
        if entity in text:
            entity_count += 1

    if entity_count >= 1:
        score += 1

    if entity_count >= 2:
        score += 1

    # Rumours are slightly lower priority
    if is_rumour(title):
        score -= 1

    return score


def get_entities(title):
    text = title.lower()

    found = set()

    for entity in FOOTBALL_ENTITIES:
        if entity in text:
            found.add(entity)

    return found


# ============================================================
# DUPLICATE DETECTION
# ============================================================

def normalize_words(title):
    title = title.lower()

    title = re.sub(r"[^a-z0-9\s]", " ", title)

    words = title.split()

    # Ignore very common words
    stopwords = {
        "the",
        "a",
        "an",
        "to",
        "of",
        "and",
        "in",
        "on",
        "for",
        "with",
        "after",
        "from",
        "as",
        "at",
        "by",
        "is",
        "are",
        "has",
        "have",
        "this",
        "that",
    }

    return set(
        word
        for word in words
        if len(word) > 2 and word not in stopwords
    )


def are_duplicates(article1, article2):
    words1 = normalize_words(article1["title"])
    words2 = normalize_words(article2["title"])

    if not words1 or not words2:
        return False

    intersection = words1.intersection(words2)

    smaller = min(len(words1), len(words2))

    if smaller > 0:
        overlap = len(intersection) / smaller

        if overlap >= 0.70:
            return True

    entities1 = get_entities(article1["title"])
    entities2 = get_entities(article2["title"])

    shared_entities = entities1.intersection(entities2)

    if len(shared_entities) >= 2:
        return True

    return False


# ============================================================
# FEED COLLECTION
# ============================================================

def fetch_source(source):
    print(f"🔎 Checking {source['name']}...")

    try:
        feed = feedparser.parse(source["url"])

    except Exception as error:
        print(f"❌ {source['name']} error: {error}")
        return []

    articles = []

    for entry in feed.entries[:100]:

        title = clean_text(
            entry.get("title", "")
        )

        link = entry.get("link", "").strip()

        summary = clean_text(
            entry.get("summary", "")
        )

        if not title or not link:
            continue

        # Safety check:
        # only accept articles whose URL belongs
        # to the trusted publisher.
        if not is_trusted_domain(
            link,
            source["domains"]
        ):
            continue

        article = {
            "title": title,
            "link": link,
            "source": source["name"],
            "summary": summary,
            "rumour": is_rumour(title),
            "score": importance_score(title),
        }

        # Football/news quality filter
        if not is_good_news(title):
            continue

        articles.append(article)

    print(
        f"   {source['name']} found "
        f"{len(articles)} usable articles"
    )

    return articles


# ============================================================
# MAIN COLLECTOR
# ============================================================

def collect_news():

    print("")
    print("===================================")
    print("📰 MATCHWIRE NEWS COLLECTOR")
    print("===================================")

    all_articles = []

    # --------------------------------------------------------
    # Collect from every trusted source
    # --------------------------------------------------------

    for source in SOURCES:

        articles = fetch_source(source)

        all_articles.extend(articles)

    print("")
    print(
        f"📰 Total usable articles: "
        f"{len(all_articles)}"
    )

    # --------------------------------------------------------
    # Remove duplicate stories
    # --------------------------------------------------------

    unique_articles = []

    duplicate_count = 0

    for article in all_articles:

        duplicate = False

        for existing in unique_articles:

            if are_duplicates(
                article,
                existing
            ):

                duplicate_count += 1

                # Keep the higher-scoring article
                if article["score"] > existing["score"]:

                    unique_articles.remove(existing)

                    unique_articles.append(
                        article
                    )

                duplicate = True

                break

        if not duplicate:
            unique_articles.append(article)

    print(
        f"🔁 Duplicate stories removed: "
        f"{duplicate_count}"
    )

    # --------------------------------------------------------
    # Only important stories
    # --------------------------------------------------------

    important_articles = [
        article
        for article in unique_articles
        if article["score"] >= 2
    ]

    # --------------------------------------------------------
    # Sort newest/important stories first
    # --------------------------------------------------------

    important_articles.sort(
        key=lambda article: article["score"],
        reverse=True
    )

    print(
        f"⭐ Important stories: "
        f"{len(important_articles)}"
    )

    print("")
    print("TOP MATCHWIRE STORIES")
    print("-----------------------------------")

    for index, article in enumerate(
        important_articles[:20],
        start=1
    ):

        rumour = "⚠️ RUMOUR" if article["rumour"] else "✅"

        print(
            f"{index}. {rumour} "
            f"[{article['score']}] "
            f"{article['title']}"
        )

        print(
            f"   🗞 {article['source']}"
        )

    print("-----------------------------------")
    print("")

    return important_articles


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    articles = collect_news()

    print("")
    print(
        f"✅ Collector finished: "
        f"{len(articles)} stories ready"
    )
