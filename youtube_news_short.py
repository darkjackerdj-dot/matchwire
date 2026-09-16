import json
import sys
import feedparser
import html
import re
import subprocess
from pathlib import Path
import textwrap
from PIL import Image, ImageDraw, ImageFont

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
    ("The Guardian", "https://www.theguardian.com/football/rss"),
]

FOOTBALL_WORDS = [
    "football", "soccer", "premier league",
    "champions league", "europa league", "uefa",
    "fifa", "transfer", "manager", "striker",
    "midfielder", "defender", "goalkeeper",
    "arsenal", "chelsea", "liverpool",
    "manchester", "barcelona", "real madrid",
    "bayern", "psg", "milan", "inter", "juventus"
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

def get_latest_news():

    articles = []

    print("📰 Checking Matchwire sources...")

    for source, url in FEEDS:

        try:

            feed = feedparser.parse(url)

            for entry in feed.entries[:10]:

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

                articles.append({
                    "source": source,
                    "title": title,
                    "summary": summary,
                    "link": link
                })

            print(f"   ✅ {source}")

        except Exception as e:
            print(f"   ⚠️ {source}: {e}")

    if not articles:
        raise RuntimeError(
            "No football news found."
        )

    return articles[0]


# ==========================================
# CREATE SLIDE
# ==========================================

def create_slide(index, article):

    img = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        (8, 13, 18)
    )

    draw = ImageDraw.Draw(img)

    # Subtle background
    for y in range(HEIGHT):
        value = int(
            8 + (y / HEIGHT) * 13
        )

        draw.line(
            [(0, y), (WIDTH, y)],
            fill=(value, value + 5, value + 9)
        )

    # Top accent
    draw.rectangle(
        (60, 80, 1020, 88),
        fill=(0, 220, 195)
    )

    # Bottom accent
    draw.rectangle(
        (60, 1832, 1020, 1840),
        fill=(0, 220, 195)
    )

    brand = font(70, True)
    label = font(36, True)
    title_font = font(60, True)
    body = font(38)
    small = font(30)

    # ======================================
    # SLIDE 1 — BREAKING
    # ======================================

    if index == 1:

        centered(
            draw,
            "MATCHWIRE",
            260,
            brand,
            (240, 245, 245)
        )

        centered(
            draw,
            "FOOTBALL NEWS",
            390,
            label,
            (0, 220, 195)
        )

        centered(
            draw,
            "LATEST UPDATE",
            650,
            font(52, True),
            (240, 240, 240)
        )

        centered(
            draw,
            article["source"].upper(),
            760,
            label,
            (170, 180, 185)
        )

        centered(
            draw,
            "NEWS ALERT",
            1080,
            font(74, True),
            (0, 220, 195)
        )

        centered(
            draw,
            "Stay updated.",
            1200,
            body,
            (220, 225, 228)
        )

        centered(
            draw,
            "Stay informed.",
            1260,
            body,
            (220, 225, 228)
        )

    # ======================================
    # SLIDE 2 — HEADLINE
    # ======================================

    elif index == 2:

        draw.text(
            (90, 250),
            "HEADLINE",
            font=label,
            fill=(0, 220, 195)
        )

        lines = wrap_lines(
            article["title"],
            25
        )

        y = 450

        for line in lines[:7]:

            centered(
                draw,
                line,
                y,
                title_font,
                (245, 248, 248)
            )

            y += 92

        draw.rectangle(
            (150, y + 60, 930, y + 65),
            fill=(0, 220, 195)
        )

        centered(
            draw,
            article["source"],
            y + 120,
            small,
            (170, 180, 185)
        )

    # ======================================
    # SLIDE 3 — MATCHWIRE BRIEF
    # ======================================

    elif index == 3:

        draw.text(
            (90, 250),
            "MATCHWIRE BRIEF",
            font=label,
            fill=(0, 220, 195)
        )

        centered(
            draw,
            "WHAT YOU NEED TO KNOW",
            470,
            font(50, True),
            (240, 245, 245)
        )

        brief = [
            "A new football story",
            "has been reported.",
            "",
            "Matchwire gives you",
            "the key headline quickly,",
            "with a direct source link."
        ]

        y = 700

        for line in brief:

            if not line:
                y += 35
                continue

            centered(
                draw,
                line,
                y,
                body,
                (215, 222, 225)
            )

            y += 70

    # ======================================
    # SLIDE 4 — SOURCE / CTA
    # ======================================

    else:

        centered(
            draw,
            "READ THE FULL STORY",
            500,
            font(54, True),
            (240, 245, 245)
        )

        centered(
            draw,
            "ORIGINAL SOURCE",
            650,
            label,
            (0, 220, 195)
        )

        centered(
            draw,
            article["source"],
            760,
            font(48, True),
            (230, 235, 237)
        )

        centered(
            draw,
            "Follow Matchwire",
            1120,
            font(60, True),
            (240, 245, 245)
        )

        centered(
            draw,
            "@matchwirenews",
            1230,
            font(42),
            (0, 220, 195)
        )

        centered(
            draw,
            "FAST  •  RELIABLE  •  SOURCE-LINKED",
            1450,
            small,
            (190, 200, 203)
        )

        centered(
            draw,
            "Football news, without the noise.",
            1540,
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
