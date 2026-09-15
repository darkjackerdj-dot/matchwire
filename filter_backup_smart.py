import re


# ============================================================
# RUMOUR / SPECULATION WORDS
# ============================================================

RUMOUR_WORDS = [
    "rumor",
    "rumour",
    "rumors",
    "rumours",
    "reportedly",
    "could join",
    "could leave",
    "could move",
    "may join",
    "may leave",
    "might join",
    "might leave",
    "interested in",
    "interest in",
    "interested",
    "linked with",
    "linked to",
    "target",
    "targets",
    "targeting",
    "considering",
    "set to join",
    "set to leave",
    "close to joining",
    "close to leaving",
    "expected to join",
    "expected to leave",
]


# ============================================================
# NON-NEWS / LOW-VALUE CONTENT
# ============================================================

GENERIC_WORDS = [
    "daily quiz",
    "daily quizzes",
    "football quiz",
    "football quizzes",
    "quiz",
    "quizzes",
    "test your knowledge",
    "flex your football brain",
    "play our game",
    "play the game",
    "fantasy football",
    "fantasy team",
    "team of the week",
    "player ratings",
    "power rankings",
    "rankings",
    "weekly preview",
    "weekend preview",
    "match preview",
    "season preview",
    "what to watch",
    "how to watch",
    "football app",
    "essential football app",
    "download the app",
    "newsletter",
    "podcast",
    "watch now",
    "video",
]


# ============================================================
# OPINION / ANALYSIS CONTENT
# ============================================================

OPINION_WORDS = [
    "overreactions",
    "overreaction",
    "hot seat index",
    "power ranking",
    "power rankings",
    "two-team title race",
    "title race already",
    "is the premier league",
    "is football",
    "what we learned",
    "what does it mean",
    "what it means",
    "why it matters",
    "analysis:",
    "analysis -",
    "opinion:",
    "opinion -",
    "reaction:",
    "reaction -",
    "explained:",
    "explained -",
]


# ============================================================
# FOOTBALL KEYWORDS
# ============================================================

FOOTBALL_WORDS = [

    # Competitions
    "football",
    "soccer",
    "premier league",
    "champions league",
    "europa league",
    "conference league",
    "world cup",
    "club world cup",
    "fa cup",
    "carabao cup",
    "league cup",

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
    "atletico madrid",
    "bayern",
    "borussia dortmund",
    "psg",
    "juventus",
    "inter milan",
    "ac milan",
    "santos",

    # Players
    "neymar",
    "messi",
    "ronaldo",
    "mbappe",
    "haaland",
    "salah",
    "kane",
    "vinicius",
    "bellingham",
    "rodri",
    "coutinho",
    "richarlison",

    # Genuine football events
    "transfer",
    "transfers",
    "signed",
    "signs",
    "signing",
    "joins",
    "joined",
    "leaves",
    "left",
    "squad",
    "selected",
    "selection",
    "appointed",
    "sacked",
    "dismissed",
    "resigned",
    "injury",
    "injured",
    "suspension",
    "suspended",
    "goal",
    "goals",
    "match",
    "win",
    "wins",
    "won",
    "defeat",
    "lost",
    "draw",
    "drawn",
    "penalty",
    "var",
    "referee",
    "final",
]


# ============================================================
# CLEAN TITLE
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
# RUMOUR DETECTION
# ============================================================

def is_rumour(title):

    cleaned = clean_title(title)

    for word in RUMOUR_WORDS:

        if word in cleaned:
            return True

    return False


# ============================================================
# GENERIC CONTENT DETECTION
# ============================================================

def is_generic(title):

    cleaned = clean_title(title)

    for word in GENERIC_WORDS:

        if word in cleaned:
            return True

    return False


# ============================================================
# OPINION / ANALYSIS DETECTION
# ============================================================

def is_opinion(title):

    cleaned = clean_title(title)

    for word in OPINION_WORDS:

        if word in cleaned:
            return True

    return False


# ============================================================
# FOOTBALL RELEVANCE
# ============================================================

def is_football_news(title):

    cleaned = clean_title(title)

    for word in FOOTBALL_WORDS:

        if word in cleaned:
            return True

    return False


# ============================================================
# FINAL QUALITY FILTER
# ============================================================

def is_good_news(title):

    if not title:
        return False

    # Must be football related
    if not is_football_news(title):
        return False

    # Remove quizzes / promotional / generic content
    if is_generic(title):
        return False

    # Remove obvious opinion / ranking / reaction articles
    if is_opinion(title):
        return False

    return True


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_titles = [

        "Coutinho joins Neymar at Santos",

        "Arsenal interested in Liverpool teenager",

        "Liverpool win Premier League match",

        "Flex your football brain with our daily quizzes",

        "Premier League weekend preview",

        "Premier League overreactions: Title race already down to two teams?",

        "Hot Seat Index: Which Premier League managers will be fired first?",

        "Mbappe stars with two goals in Madrid win",

        "Player could join Chelsea",

        "Pocognoli announces first Scotland squad",

        "VAR from Manchester derby stood down from duty",

    ]


    print("\n===================================")
    print("       MATCHWIRE FILTER TEST")
    print("===================================\n")


    for title in test_titles:

        print(f"📰 {title}")

        print(
            f"Football: "
            f"{'YES ✅' if is_football_news(title) else 'NO ❌'}"
        )

        print(
            f"Rumour: "
            f"{'YES ⚠️' if is_rumour(title) else 'NO ✅'}"
        )

        print(
            f"Generic: "
            f"{'YES ❌' if is_generic(title) else 'NO ✅'}"
        )

        print(
            f"Opinion: "
            f"{'YES ❌' if is_opinion(title) else 'NO ✅'}"
        )

        print(
            f"KEEP: "
            f"{'YES ✅' if is_good_news(title) else 'NO ❌'}"
        )

        print("-----------------------------------")
