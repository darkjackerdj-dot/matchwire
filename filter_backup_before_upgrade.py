import re


# ============================================================
# RUMOUR / SPECULATION
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
# GENERIC / LOW VALUE CONTENT
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
# OPINION / ANALYSIS
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
    "verdict:",
    "verdict -",
]


# ============================================================
# SOCIAL MEDIA / REACTION CONTENT
# ============================================================

SOCIAL_REACTION_WORDS = [
    "posts crying emoji",
    "posts crying",
    "posts laughing emoji",
    "posts laughing",
    "posts emoji",
    "emoji after",
    "tweets",
    "tweeted",
    "posts on x",
    "posted on x",
    "social media",
    "instagram post",
    "instagram story",
    "social media post",
    "fans react",
    "fan reaction",
    "fans react to",
    "fans respond",
    "reacts on social media",
]


# ============================================================
# DISCUSSION / FEATURE CONTENT
# ============================================================

DISCUSSION_WORDS = [
    "will fans ever",
    "can fans ever",
    "what fans think",
    "fans ever get to",
    "why fans",
    "should fans",
    "could fans",
    "what does this mean",
    "what it means for",
    "everything you need to know",
    "all you need to know",
    "five things",
    "five things we learned",
    "things to know",
    "key questions",
    "questions answered",
]


# ============================================================
# FOOTBALL KEYWORDS
# ============================================================

FOOTBALL_WORDS = [
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
    "vinicius",
    "bellingham",
    "rodri",
    "coutinho",
    "richarlison",

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
    "surgery",

    "suspension",
    "suspended",
    "banned",
    "ban",

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
# TITLE CLEANING
# ============================================================

def clean_title(title):

    title = title.lower()

    title = re.sub(
        r"\s*[-|]\s*"
        r"(bbc sport|espn|espn fc|fotmob|sofascore)"
        r"\s*$",
        "",
        title,
        flags=re.IGNORECASE
    )

    title = re.sub(
        r"[^a-z0-9\s]",
        " ",
        title
    )

    return " ".join(
        title.split()
    )


# ============================================================
# RUMOUR CHECK
# ============================================================

def is_rumour(title):

    cleaned = clean_title(title)

    for word in RUMOUR_WORDS:

        if word in cleaned:
            return True

    return False


# ============================================================
# GENERIC CHECK
# ============================================================

def is_generic(title):

    cleaned = clean_title(title)

    for word in GENERIC_WORDS:

        if word in cleaned:
            return True

    return False


# ============================================================
# OPINION CHECK
# ============================================================

def is_opinion(title):

    cleaned = clean_title(title)

    for word in OPINION_WORDS:

        if word in cleaned:
            return True

    return False


# ============================================================
# SOCIAL REACTION CHECK
# ============================================================

def is_social_reaction(title):

    cleaned = clean_title(title)

    for word in SOCIAL_REACTION_WORDS:

        if word in cleaned:
            return True

    return False


# ============================================================
# DISCUSSION / FEATURE CHECK
# ============================================================

def is_discussion(title):

    cleaned = clean_title(title)

    for word in DISCUSSION_WORDS:

        if word in cleaned:
            return True

    return False


# ============================================================
# FOOTBALL CHECK
# ============================================================

def is_football_news(title):

    cleaned = clean_title(title)

    for word in FOOTBALL_WORDS:

        if word in cleaned:
            return True

    return False


# ============================================================
# FINAL QUALITY CHECK
# ============================================================

def is_good_news(title):

    if not title:
        return False


    # Must actually be football related
    if not is_football_news(title):
        return False


    # Remove generic content
    if is_generic(title):
        return False


    # Remove opinion / analysis
    if is_opinion(title):
        return False


    # Remove social-media reaction stories
    if is_social_reaction(title):
        return False


    # Remove discussion / feature stories
    if is_discussion(title):
        return False


    return True


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_titles = [

        # GOOD
        "Coutinho joins Neymar at Santos",
        "Liverpool win Premier League match",
        "Mbappe stars with two goals in Madrid win",
        "Manchester United appoint new manager",
        "Arsenal sign new midfielder",
        "Player suffers serious injury",
        "Scotland announce new squad",

        # RUMOUR
        "Arsenal interested in Liverpool teenager",
        "Player could join Chelsea",

        # LOW VALUE
        "Flex your football brain with our daily quizzes",
        "Premier League weekend preview",
        "Premier League overreactions: Title race already down to two teams?",
        "Hot Seat Index: Which Premier League managers will be fired first?",

        # SOCIAL MEDIA
        "Richarlison posts crying emoji after being left out",
        "Player reacts on social media",

        # DISCUSSION
        "Will fans ever get to hear live VAR audio?",
        "Everything you need to know about the match",
    ]


    print("")
    print("===================================")
    print("       MATCHWIRE FILTER TEST")
    print("===================================")
    print("")


    for title in test_titles:

        print(
            f"📰 {title}"
        )

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
            f"Social: "
            f"{'YES ❌' if is_social_reaction(title) else 'NO ✅'}"
        )

        print(
            f"Discussion: "
            f"{'YES ❌' if is_discussion(title) else 'NO ✅'}"
        )

        print(
            f"KEEP: "
            f"{'YES ✅' if is_good_news(title) else 'NO ❌'}"
        )

        print("-----------------------------------")
