import re

RUMOUR_WORDS = [
    "rumour","rumor","reportedly","reports suggest","reports claim",
    "could join","could leave","could move","may join","may leave",
    "might join","might leave","interested in","interest in","linked with",
    "linked to","eyeing","considering","targeting","set to join",
    "set to leave","expected to join","expected to leave",
]

GENERIC_WORDS = [
    "no weekend game",
    "no game for",
    "no match for",
    "officials",
    "refereeing",
    "referee appointments",
    "referee appointment",
    "quiz",
    "quiz:",
    "preview",
    "pre-match",
    "match preview",
    "weekend preview",
    "watch:",
    "five things",
    "five things we learned",
    "things to know",
    "key questions",
    "questions answered",
    "everything you need to know",
    "all you need to know",
    "team of the week",
    "player of the week",
    "power rankings",
    "ratings",
    "ranking",
    "rankings",
    "best goals",
    "best moments",
    "highlights",
    "all the goals",
    "goals from",

    # Low-value / generic articles
    "sutton's predictions",
    "predictions",
    "manager ins and outs",
    "ins and outs",
    "meet ",
    "penalty killer",

    # Explainers / FAQs / rule articles
    "what are the premier league rules",
    "what is the premier league's",
    "what is the premier league",
    "why are there europa league matches",
    "why have the premier league announced",
    "why is sunderland vs arsenal",
    "how do european squad lists work",
    "how does it work",
    "rules on",
    "rules for",
    "how do",
    "how does",
]

OPINION_WORDS = [
    "opinion","analysis","column","editorial","verdict","overreaction",
    "overreactions","debate","should","could have","was wrong",
    "got it wrong","get it wrong","power ranking","hot seat","index",
    "assessment",
]

SOCIAL_REACTION_WORDS = [
    "posts crying emoji","posts crying","posts laughing emoji",
    "posts laughing","posts emoji","emoji after","tweets","tweeted",
    "posts on x","posted on x","social media","instagram post",
    "instagram story","social media post","fans react","fan reaction",
    "fans react to","fans respond","reacts on social media",
]

DISCUSSION_WORDS = [
    "will fans ever","can fans ever","what fans think","fans ever get to",
    "why fans","should fans","could fans","what does this mean",
    "what it means for","everything you need to know",
    "all you need to know","five things","five things we learned",
    "things to know","key questions","questions answered",
]

EXPLAINER_START_WORDS = [
    "why ","how ","what ","when ","where ","who ","which ","can ",
    "could ","should ","will ","does ","do ","is ","are ",
]

FOOTBALL_WORDS = [
    "football","soccer","premier league","champions league","europa league",
    "conference league","world cup","fa cup","league cup","la liga",
    "bundesliga","serie a","ligue 1","club world cup",

    "arsenal","chelsea","liverpool","manchester united","manchester city",
    "tottenham","newcastle","aston villa","everton","west ham","brighton",
    "fulham","crystal palace","nottingham forest","wolves","bournemouth",
    "brentford","leeds","sunderland",

    "real madrid","barcelona","atletico madrid","bayern",
    "borussia dortmund","psg","paris saint-germain","juventus",
    "inter milan","ac milan","napoli","roma",

    "santos","neymar","coutinho",

    "manager","coach","player","players","striker","midfielder",
    "defender","goalkeeper","referee","var","transfer","transfers",
    "injury","injured","squad","match","goal","goals",
]


def normalize(text):
    return re.sub(r"\s+", " ", text.lower().strip())


def is_rumour(title):
    text = normalize(title)
    return any(word in text for word in RUMOUR_WORDS)


def is_good_news(title):
    text = normalize(title)

    # Must contain football-related content
    if not any(word in text for word in FOOTBALL_WORDS):
        return False

    # Remove generic / low-value articles
    if any(word in text for word in GENERIC_WORDS):
        return False

    # Remove opinion / analysis pieces
    if any(word in text for word in OPINION_WORDS):
        return False

    # Remove social-media reaction articles
    if any(word in text for word in SOCIAL_REACTION_WORDS):
        return False

    # Remove discussion / explainer-style articles
    if any(word in text for word in DISCUSSION_WORDS):
        return False

    return True
