import json
import sys
import feedparser
import html
import re
import subprocess
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageOps

# ==========================================
# MATCHWIRE — ANIMATED NEWS SHORT
# ==========================================

WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION = 30

OUTPUT = "matchwire_news_short.mp4"

FEEDS = [
    ("BBC Sport", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
    ("ESPN", "https://www.espn.com/espn/rss/soccer/news"),
]

FOOTBALL_WORDS = [
    "football", "soccer",
    "premier league", "champions league",
    "europa league", "conference league",
    "world cup", "euro", "euros",
    "nations league", "qualifier", "qualifiers",
    "international", "friendly", "fixture", "fixtures",
    "fa cup", "carabao cup", "efl cup",
    "championship", "league one", "league two",
    "bundesliga", "serie a", "serie b",
    "la liga", "ligue 1",
    "mls", "nwsl",
    "afcon", "african cup",
    "copa america", "copa del rey",
    "concacaf", "conmebol", "afc",
    "uefa", "fifa",
    "transfer", "manager", "coach",
    "striker", "forward", "winger",
    "midfielder", "defender", "centre-back",
    "center-back", "full-back", "goalkeeper",
    "captain", "player", "players",
    "goal", "goals", "scored", "scores",
    "assist", "assists",
    "match", "matches", "win", "wins",
    "defeat", "defeated", "draw",
    "penalty", "penalties", "shootout", "shoot-out",
    "extra time", "red card", "yellow card",
    "var", "offside", "clean sheet",
    "lineup", "line-up", "starting xi",
    "substitute", "substitution", "squad",
    "injury", "injured", "fitness",
    "relegation", "promotion", "playoff", "playoffs",
    "women's football", "women's",
    "women football",
    "youth football", "u21", "u20", "u19", "u18",
    "arsenal", "chelsea", "liverpool",
    "manchester united", "manchester city",
    "tottenham", "newcastle", "aston villa",
    "everton", "west ham", "brighton",
    "fulham", "crystal palace", "nottingham forest",
    "wolves", "bournemouth", "brentford",
    "leeds", "sunderland",
    "real madrid", "barcelona", "atletico madrid",
    "bayern", "borussia dortmund",
    "psg", "paris saint-germain",
    "juventus", "inter milan", "ac milan",
    "napoli", "roma", "neymar",
]


# ==========================================
# TEXT HELPERS
# ==========================================

def clean_text(text):
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_football(title, summary):
    text = f"{title} {summary}".lower()
    return any(word in text for word in FOOTBALL_WORDS)


def font(size, bold=False):
    if bold:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    else:
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    return ImageFont.truetype(path, size)


def centered(draw, text, y, fnt, fill):
    box = draw.textbbox((0, 0), text, font=fnt)
    w = box[2] - box[0]

    draw.text(
        ((WIDTH - w) // 2, y),
        text,
        font=fnt,
        fill=fill
    )


def wrap_lines(text, width):
    return textwrap.wrap(
        text,
        width=width,
        break_long_words=False
    )


# ==========================================
# GET NEWS
# ==========================================


def get_besoccer_news():
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    articles = []

    url = "https://www.besoccer.com/news/latest"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        for item in soup.select(
            "li.news-vertical, li.news-horizontal"
        ):
            link_tag = item.select_one(
                "a.news[href]"
            )

            headline = item.select_one(
                'h3[itemprop="headline"]'
            )

            teaser = item.select_one(
                "p.teaser"
            )

            published = item.select_one(
                'meta[itemprop="datePublished"]'
            )

            if not link_tag or not headline:
                continue

            title = clean_text(
                headline.get_text(" ", strip=True)
            )

            link = urljoin(
                url,
                link_tag.get("href", "")
            )

            summary = ""

            if teaser:
                summary = clean_text(
                    teaser.get_text(" ", strip=True)
                )

            published_dt = None

            if published:
                raw_date = published.get(
                    "content",
                    ""
                ).strip()

                if raw_date:
                    try:
                        published_dt = datetime.fromisoformat(
                            raw_date.replace(
                                "Z",
                                "+00:00"
                            )
                        )
                    except Exception:
                        published_dt = None

            if not title or not link:
                continue

            # BeSoccer is football-only.
            # No FOOTBALL_WORDS filter.

            score = 4

            text_lower = (
                f"{title} {summary}"
            ).lower()

            # BeSoccer scoring keywords.
            # No football keyword filter is applied.
            besoccer_news_words = [
                "transfer", "signed", "signs", "joins", "leaves",
                "appointed", "sacked", "injury", "injured",
                "returns", "contract", "deal", "agrees",
                "confirmed", "announced", "goal", "goals",
                "win", "wins", "defeat", "draw", "match",
                "champions league", "premier league",
                "europa league", "world cup", "cup",
                "manager", "managerial"
            ]

            for word in besoccer_news_words:
                if word in text_lower:
                    score += 2

            if len(summary) >= 120:
                score += 2

            if len(summary) >= 250:
                score += 1

            if len(title) >= 45:
                score += 1

            if published_dt:
                age_hours = (
                    datetime.now(timezone.utc)
                    - published_dt
                ).total_seconds() / 3600

                if age_hours > 48:
                    continue

                if age_hours <= 6:
                    score += 8
                elif age_hours <= 12:
                    score += 6
                elif age_hours <= 24:
                    score += 4
                elif age_hours <= 36:
                    score += 2

            articles.append({
                "source": "BeSoccer",
                "title": title,
                "summary": summary,
                "link": link,
                "score": score
            })

        print(
            f"   ✅ BeSoccer ({len(articles)} articles)"
        )

    except Exception as e:
        print(f"   ⚠️ BeSoccer: {e}")

    return articles


def extract_entry_image(entry):
    import html as html_lib
    from urllib.parse import urljoin

    def clean_url(value):
        if not value:
            return None

        value = html_lib.unescape(str(value)).strip()

        if value.startswith("//"):
            value = "https:" + value

        return value

    def check_value(value):
        if isinstance(value, str):
            value = clean_url(value)

            if value and any(
                ext in value.lower()
                for ext in [".jpg", ".jpeg", ".png", ".webp", ".avif"]
            ):
                return value

        if isinstance(value, dict):
            for key in (
                "url",
                "href",
                "src",
                "image",
                "image_url",
                "imagehref",
                "content",
            ):
                result = check_value(value.get(key))
                if result:
                    return result

        if isinstance(value, (list, tuple)):
            for item in value:
                result = check_value(item)
                if result:
                    return result

        return None

    # media:content
    result = check_value(entry.get("media_content"))
    if result:
        return result

    # media:thumbnail
    result = check_value(entry.get("media_thumbnail"))
    if result:
        return result

    # media:group / nested media data
    result = check_value(entry.get("media_group"))
    if result:
        return result

    # RSS image fields
    result = check_value(entry.get("image"))
    if result:
        return result

    # RSS links / enclosures
    links = entry.get("links") or []

    for item in links:
        if not isinstance(item, dict):
            continue

        href = clean_url(item.get("href"))
        item_type = str(item.get("type") or "").lower()
        rel = str(item.get("rel") or "").lower()

        if href and (
            item_type.startswith("image/")
            or rel == "enclosure"
            or any(
                ext in href.lower()
                for ext in [".jpg", ".jpeg", ".png", ".webp", ".avif"]
            )
        ):
            return href

    # Search RSS HTML for <img src="...">
    raw_html = str(
        entry.get("summary", "")
        or entry.get("description", "")
        or entry.get("content", "")
    )

    img_matches = re.findall(
        r'<img[^>]+(?:src|data-src|data-original)=[\'"]([^\'"]+)[\'"]',
        raw_html,
        re.I
    )

    for value in img_matches:
        result = clean_url(value)

        if result:
            return result

    # Also search HTML for direct image URLs
    direct_matches = re.findall(
        r'https?://[^"\']+\.(?:jpg|jpeg|png|webp|avif)(?:\?[^"\']*)?',
        raw_html,
        re.I
    )

    for value in direct_matches:
        result = clean_url(value)

        if result:
            return result

    return None


def get_latest_news():

    articles = []

    print("📰 Checking Matchwire sources...")

    # Words that usually indicate low-value or speculative stories
    LOW_VALUE_WORDS = [
        "rumour", "rumor", "gossip", "quiz", "rating",
        "ratings", "predicted", "prediction", "dream team",
        "best xi", "power ranking", "reaction", "opinion",
        "watch", "live blog", "explained", "explainer"
    ]

    # Strong news signals
    NEWS_WORDS = [
        "transfer", "signed", "signs", "joins", "leaves",
        "appointed", "sacked", "injury", "injured",
        "returns", "contract", "deal", "agrees",
        "confirmed", "announced", "goal", "goals",
        "win", "wins", "defeat", "draw", "match",
        "champions league", "premier league", "europa league",
        "world cup", "cup", "manager", "managerial"
    ]

    for source, url in FEEDS:

        try:

            feed = feedparser.parse(url)

            for entry in feed.entries[:20]:

                title = clean_text(
                    entry.get("title", "")
                )

                summary = clean_text(
                    entry.get("summary", "")
                    or entry.get("description", "")
                )

                link = entry.get("link", "")

                if not title or not link:
                    continue

                if not is_football(title, summary):
                    continue

                text_lower = f"{title} {summary}".lower()

                # Skip obvious low-value/speculative stories
                if any(word in text_lower for word in LOW_VALUE_WORDS):
                    continue

                # Calculate a simple news-quality score
                score = 0

                # Strong football-news signals
                for word in NEWS_WORDS:
                    if word in text_lower:
                        score += 2

                # Prefer stories with useful summaries
                if len(summary) >= 120:
                    score += 2

                if len(summary) >= 250:
                    score += 1

                # Prefer specific headlines over very short ones
                if len(title) >= 45:
                    score += 1

                # Freshness scoring
                published_time = entry.get("published_parsed")

                if published_time:
                    try:
                        published_dt = datetime(
                            *published_time[:6],
                            tzinfo=timezone.utc
                        )

                        age_hours = (
                            datetime.now(timezone.utc) - published_dt
                        ).total_seconds() / 3600

                        # Ignore stories older than 48 hours
                        if age_hours > 48:
                            continue

                        # Give newer stories a stronger priority
                        if age_hours <= 6:
                            score += 8
                        elif age_hours <= 12:
                            score += 6
                        elif age_hours <= 24:
                            score += 4
                        elif age_hours <= 36:
                            score += 2

                    except Exception:
                        pass

                # When running through YouTube automation, skip stories
                # that have already been uploaded and continue to the next one.
                if "--skip-seen" in sys.argv:
                    seen_file = Path("youtube_seen.json")
                    if seen_file.exists():
                        try:
                            seen = json.loads(
                                seen_file.read_text()
                            )
                        except Exception:
                            seen = []

                        story_key = (
                            title.strip().lower()
                            + "|"
                            + link.strip()
                        )

                        if story_key in seen:
                            continue

                articles.append({
                    "source": source,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "image": extract_entry_image(entry),
                    "score": score
                })

            print(f"   ✅ {source}")

        except Exception as e:
            print(f"   ⚠️ {source}: {e}")

    # Add BeSoccer separately.
    # BeSoccer is football-only, so no
    # FOOTBALL_WORDS filter is applied.
    besoccer_articles = []

    # Apply the same YouTube duplicate-history protection
    # to BeSoccer stories.
    if "--skip-seen" in sys.argv:
        seen_file = Path("youtube_seen.json")

        if seen_file.exists():
            try:
                seen = json.loads(seen_file.read_text())
            except Exception:
                seen = []
        else:
            seen = []

        filtered_besoccer = []

        for article in besoccer_articles:
            story_key = (
                article["title"].strip().lower()
                + "|"
                + article["link"].strip()
            )

            if story_key in seen:
                continue

            filtered_besoccer.append(article)

        besoccer_articles = filtered_besoccer

    articles.extend(besoccer_articles)

    if not articles:
        raise RuntimeError(
            "No suitable football news found."
        )

    # Highest-quality story first.
    # Original RSS order is used as the tie-breaker.
    articles.sort(
        key=lambda article: article["score"],
        reverse=True
    )

    selected = articles[0]

    print(f"   🎯 Quality score: {selected['score']}")

    return selected


# ==========================================
# CREATE SLIDE
# ==========================================
def extract_page_og_image(article_url):
    """Fetch the article page and extract og:image / twitter:image."""

    if not article_url:
        return None

    try:
        request = urllib.request.Request(
            article_url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 "
                    "Chrome/140 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,"
                    "application/xml;q=0.9,*/*;q=0.8"
                ),
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:
            html = response.read().decode(
                "utf-8",
                errors="ignore"
            )

        patterns = [
            r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        ]

        for pattern in patterns:
            match = re.search(
                pattern,
                html,
                re.I
            )

            if match:
                image_url = match.group(1).strip()

                if image_url.startswith("//"):
                    image_url = "https:" + image_url

                print(
                    "🖼️ Article page image found."
                )

                return image_url

    except Exception as e:
        print(
            f"⚠️ Article page image lookup failed: {e}"
        )

    return None


def load_article_image(article):
    cached = article.get("_image_path")

    if cached and Path(cached).exists():
        return cached

    image_url = article.get("image")

    # RSS image is missing on some ESPN stories.
    # Fall back to the article page's og:image.
    if not image_url:
        image_url = extract_page_og_image(
            article.get("link", "")
        )

        if image_url:
            article["image"] = image_url

    if not image_url:
        return None

    try:
        request = urllib.request.Request(
            image_url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "image/avif,image/webp,image/jpeg,image/png,*/*",
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=15
        ) as response:
            content_type = (
                response.headers.get("Content-Type") or ""
            ).lower()

            if not content_type.startswith("image/"):
                return None

            data = response.read(8 * 1024 * 1024)

        temp_path = Path("matchwire_article_image.jpg")

        with temp_path.open("wb") as f:
            f.write(data)

        # Validate + convert to JPEG so ffmpeg/Pillow gets a predictable file.
        source_img = Image.open(temp_path).convert("RGB")

        source_img.save(
            temp_path,
            "JPEG",
            quality=90
        )

        article["_image_path"] = str(temp_path)

        print("🖼️ Article image loaded.")
        return str(temp_path)

    except Exception as e:
        print(f"⚠️ Article image unavailable: {e}")
        return None


def draw_article_image(draw, image_path, top=120, bottom=1800, darken=120):
    if not image_path:
        return False

    try:
        img = Image.open(image_path).convert("RGB")

        available_h = bottom - top

        fitted = ImageOps.fit(
            img,
            (WIDTH, available_h),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5)
        )

        overlay = Image.new(
            "RGBA",
            fitted.size,
            (0, 0, 0, darken)
        )

        fitted = fitted.convert("RGBA")
        fitted.alpha_composite(overlay)

        image_pos = (0, top)

        # Replace existing background with the article visual.
        canvas = Image.new(
            "RGBA",
            (WIDTH, HEIGHT),
            (8, 13, 18, 255)
        )

        canvas.alpha_composite(
            fitted,
            image_pos
        )

        return canvas.convert("RGB")

    except Exception as e:
        print(f"⚠️ Image render failed: {e}")
        return False



def create_slide(index, article):

    image_path = load_article_image(article)

    # Keep the entire page on the clean Matchwire dark background.
    # The article image is shown ONLY inside the dedicated image box
    # on the first news slide.
    img = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (8, 13, 18)
    )

    draw = ImageDraw.Draw(img)

    # Strong dark bottom/top readability overlays
    draw.rectangle(
        (0, 0, WIDTH, 260),
        fill=(8, 13, 18, 230)
    )

    draw.rectangle(
        (0, 1480, WIDTH, HEIGHT),
        fill=(8, 13, 18, 235)
    )

    # Matchwire accents
    draw.rectangle(
        (60, 80, 1020, 88),
        fill=(0, 220, 195)
    )

    draw.rectangle(
        (60, 1832, 1020, 1840),
        fill=(0, 220, 195)
    )

    brand = font(66, True)
    label = font(34, True)
    title_font = font(54, True)
    body = font(34)
    small = font(28)

    title_lines = wrap_lines(
        article["title"],
        25
    )[:6]

    # ======================================
    # SLIDE 1 — NEWS FIRST
    # ======================================

    if index == 1:

        draw.text(
            (70, 135),
            "⚡ NEWS ALERT",
            font=label,
            fill=(0, 220, 195)
        )

        y = 420

        for line in title_lines:
            centered(
                draw,
                line,
                y,
                title_font,
                (250, 252, 252)
            )
            y += 82

        centered(
            draw,
            article["source"].upper(),
            1550,
            small,
            (190, 200, 203)
        )

        # ======================================
        # ARTICLE IMAGE — AFTER HEADLINE
        # ======================================
        if image_path:
            try:
                article_img = Image.open(
                    image_path
                ).convert("RGB")

                image_top = y + 25
                image_bottom = 1430
                image_width = 940
                image_height = max(
                    220,
                    image_bottom - image_top
                )

                fitted = ImageOps.fit(
                    article_img,
                    (image_width, image_height),
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5)
                )

                # Slight dark overlay for a premium look
                fitted_rgba = fitted.convert("RGBA")

                overlay = Image.new(
                    "RGBA",
                    fitted_rgba.size,
                    (0, 0, 0, 25)
                )

                fitted_rgba.alpha_composite(
                    overlay
                )

                img.paste(
                    fitted_rgba.convert("RGB"),
                    (70, image_top)
                )

                # Image border
                draw.rounded_rectangle(
                    (
                        70,
                        image_top,
                        70 + image_width,
                        image_top + image_height
                    ),
                    radius=24,
                    outline=(0, 220, 195),
                    width=4
                )

            except Exception as e:
                print(
                    f"⚠️ Slide image placement failed: {e}"
                )


        centered(
            draw,
            "MATCHWIRE",
            1640,
            brand,
            (245, 248, 248)
        )

    # ======================================
    # SLIDE 2 — IMAGE + HEADLINE
    # ======================================

    elif index == 2:

        draw.text(
            (70, 150),
            "LATEST FOOTBALL NEWS",
            font=label,
            fill=(0, 220, 195)
        )

        y = 1420

        for line in title_lines:
            centered(
                draw,
                line,
                y,
                font(46, True),
                (248, 250, 250)
            )
            y += 68

    # ======================================
    # SLIDE 3 — WHAT HAPPENED
    # ======================================

    elif index == 3:

        draw.text(
            (70, 150),
            "WHAT HAPPENED",
            font=label,
            fill=(0, 220, 195)
        )

        # Use the real feed summary when available.
        summary = article.get("summary", "").strip()

        if summary:
            summary_lines = wrap_lines(
                summary,
                42
            )[:8]

            y = 430

            for line in summary_lines:
                centered(
                    draw,
                    line,
                    y,
                    body,
                    (238, 242, 244)
                )
                y += 62
        else:
            centered(
                draw,
                "Latest football update",
                620,
                font(48, True),
                (240, 245, 245)
            )

            centered(
                draw,
                "from Matchwire.",
                700,
                body,
                (215, 222, 225)
            )

        centered(
            draw,
            f"Source: {article['source']}",
            1580,
            small,
            (180, 190, 194)
        )

    # ======================================
    # SLIDE 4 — MATCHWIRE CTA
    # ======================================

    else:

        centered(
            draw,
            "MATCHWIRE",
            520,
            font(76, True),
            (245, 248, 248)
        )

        centered(
            draw,
            "SOURCE-LINKED FOOTBALL NEWS",
            650,
            label,
            (0, 220, 195)
        )

        centered(
            draw,
            "Read the full story",
            850,
            font(48, True),
            (238, 242, 244)
        )

        centered(
            draw,
            article["source"],
            960,
            font(42, True),
            (205, 212, 215)
        )

        centered(
            draw,
            "Follow @matchwirenews",
            1190,
            font(54, True),
            (240, 245, 245)
        )

        centered(
            draw,
            "FAST  •  FOOTBALL  •  SOURCE-LINKED",
            1335,
            small,
            (190, 200, 203)
        )

        centered(
            draw,
            "Football news, without the noise.",
            1450,
            body,
            (220, 225, 228)
        )

    path = f"matchwire_slide_{index}.png"

    img.save(path)

    return path


# ==========================================
# CREATE VIDEO
# ==========================================

def create_video(slides):

    # Each slide = 7.5 seconds
    duration = 7.5

    inputs = []

    for slide in slides:

        inputs.extend([
            "-loop",
            "1",
            "-t",
            str(duration),
            "-i",
            slide
        ])

    filter_parts = []

    for i in range(len(slides)):

        filter_parts.append(
            f"[{i}:v]"
            f"scale={WIDTH}:{HEIGHT},"
            f"fps={FPS},"
            f"format=yuv420p"
            f"[v{i}]"
        )

    concat_inputs = "".join(
        f"[v{i}]" for i in range(len(slides))
    )

    filter_parts.append(
        concat_inputs +
        f"concat=n={len(slides)}:v=1:a=0[outv]"
    )

    filter_complex = ";".join(
        filter_parts
    )

    command = [
        "ffmpeg",
        "-y"
    ]

    command.extend(inputs)

    # ==========================================
    # MATCHWIRE BACKGROUND MUSIC
    # ==========================================

    BGM = "music/matchwire_bgm.mp3"

    audio_input_index = 4

    command.extend([
        "-stream_loop",
        "-1",
        "-i",
        BGM
    ])

    filter_complex += (
        f";[{audio_input_index}:a]"
        f"volume=0.18,"
        f"atrim=duration={DURATION},"
        f"afade=t=in:st=0:d=1,"
        f"afade=t=out:st={DURATION - 2}:d=2"
        f"[bgm]"
    )

    command.extend([
        "-filter_complex",
        filter_complex,

        "-map",
        "[outv]",

        "-map",
        "[bgm]",

        "-t",
        str(DURATION),

        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-pix_fmt",
        "yuv420p",

        "-c:a",
        "aac",
        "-b:a",
        "128k",

        "-movflags",
        "+faststart",

        OUTPUT
    ])

    subprocess.run(
        command,
        check=True
    )


# ==========================================
# MAIN
# ==========================================

def main():

    print()
    print("=================================")
    print("MATCHWIRE ANIMATED NEWS SHORT")
    print("=================================")
    print()

    article = None

    # Queue mode: render the exact story supplied by the
    # YouTube queue client instead of selecting a new story.
    if "--story-file" in sys.argv:
        try:
            index = sys.argv.index("--story-file")

            if index + 1 >= len(sys.argv):
                raise RuntimeError("Missing story file path")

            story_file = Path(sys.argv[index + 1])

            article = json.loads(
                story_file.read_text()
            )

            required = ["title", "source", "link"]

            for field in required:
                if field not in article:
                    raise RuntimeError(
                        f"Queued story missing field: {field}"
                    )

            print("📦 Queue story loaded.")

        except Exception as e:
            raise RuntimeError(
                f"Could not load queued story: {e}"
            )

    else:
        article = get_latest_news()

    print()
    Path("matchwire_latest.json").write_text(
        json.dumps(
            {
                "title": article["title"],
                "source": article["source"],
                "link": article["link"]
            },
            indent=2
        )
    )

    print("📰 Selected story:")
    print(article["title"])
    print()
    print("🌐 Source:", article["source"])
    print("🔗 Link:", article["link"])
    print()

    if "--metadata-only" in sys.argv:
        print("ℹ️ Metadata-only mode: skipping slide/video generation.")
        print()
        return

    slides = []

    for i in range(1, 5):

        print(f"🎨 Creating slide {i}/4...")

        slides.append(
            create_slide(
                i,
                article
            )
        )

    print()
    print("🎬 Rendering 30-second video...")

    create_video(slides)

    print()
    print("=================================")
    print("✅ MATCHWIRE SHORT READY")
    print("=================================")
    print()
    print("📁 File:", OUTPUT)
    print("📐 Size: 1080x1920")
    print("⏱️ Duration: 30 seconds")
    print("📰 Source:", article["source"])
    print()


if __name__ == "__main__":
    main()
