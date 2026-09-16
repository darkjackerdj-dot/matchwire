import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials


VIDEO = Path("matchwire_news_short.mp4")
SEEN_FILE = Path("youtube_seen.json")
METADATA_FILE = Path("matchwire_latest.json")

QUEUE_URL = "https://matchwire.darkjackerdj.workers.dev/youtube-queue"
QUEUE_TOKEN_FILE = Path(".youtube_queue_token")
QUEUE_STORY_FILE = Path("matchwire_queue_story.json")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def load_seen():
    if not SEEN_FILE.exists():
        return []

    try:
        return json.loads(SEEN_FILE.read_text())
    except Exception:
        return []


def save_seen(seen):
    SEEN_FILE.write_text(
        json.dumps(seen, indent=2)
    )


def get_queue_token():
    if not QUEUE_TOKEN_FILE.exists():
        raise FileNotFoundError(
            f"Queue token file not found: {QUEUE_TOKEN_FILE}"
        )

    return QUEUE_TOKEN_FILE.read_text().strip()


def fetch_youtube_queue():
    token = get_queue_token()

    request = urllib.request.Request(
        QUEUE_URL,
        headers={
            "X-Matchwire-Queue-Token": token,
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        if not data.get("ok"):
            raise RuntimeError(
                f"Queue API error: {data}"
            )

        return data.get("queue", [])

    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"Queue HTTP error: {e.code} {e.reason}"
        )


def acknowledge_queue_story(key):
    token = get_queue_token()

    payload = json.dumps({
        "action": "ack",
        "key": key,
    }).encode("utf-8")

    request = urllib.request.Request(
        QUEUE_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "X-Matchwire-Queue-Token": token,
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(
                response.read().decode("utf-8")
            )

        if not data.get("ok"):
            raise RuntimeError(
                f"Queue ACK failed: {data}"
            )

        print(
            f"✅ Queue ACK successful. Remaining: "
            f"{data.get('remaining', '?')}"
        )

    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f"Queue ACK HTTP error: {e.code} {e.reason}"
        )


def save_queue_story(story):
    QUEUE_STORY_FILE.write_text(
        json.dumps(story, indent=2)
    )


def create_news_short(queue_story=None):
    print("🎬 Creating Matchwire Short...")

    command = [
        "/home/dj/football-bot/venv/bin/python",
        "youtube_news_short.py",
    ]

    if queue_story is not None:
        save_queue_story(queue_story)

        command.extend([
            "--story-file",
            str(QUEUE_STORY_FILE),
        ])
    else:
        command.append("--skip-seen")

    subprocess.run(
        command,
        check=True
    )

    print("✅ Short created!")


def get_latest_story():
    if not METADATA_FILE.exists():
        return None

    try:
        data = json.loads(
            METADATA_FILE.read_text()
        )
    except Exception:
        return None

    required = ["title", "source", "link"]

    for field in required:
        if field not in data:
            return None

    return data


def fetch_latest_story():
    """
    Fetch the best suitable football story that has not been uploaded yet.
    """
    print("🔎 Checking latest football news...")

    subprocess.run(
        ["/home/dj/football-bot/venv/bin/python", "youtube_news_short.py", "--metadata-only", "--skip-seen"],
        check=True
    )

    return get_latest_story()

def upload_to_youtube(story):

    if not VIDEO.exists():
        raise FileNotFoundError(
            f"Video not found: {VIDEO}"
        )

    credentials = Credentials.from_authorized_user_file(
        "youtube_token.json",
        SCOPES
    )

    youtube = build(
        "youtube",
        "v3",
        credentials=credentials
    )

    title = story["title"].strip()
    source = story["source"].strip()
    link = story["link"].strip()

    # ---------------------------------------------
    # YouTube SEO metadata
    # ---------------------------------------------

    youtube_title = (
        f"{title} | Football News"
    )

    description = (
        "⚽ MATCHWIRE — FOOTBALL NEWS\n\n"
        f"📰 {title}\n\n"
        f"🌐 Source: {source}\n"
        f"🔗 Original story: {link}\n\n"
        "📲 Follow Matchwire for football news and updates:\n"
        "@matchwirenews\n\n"
        "Fast, reliable and source-linked football updates.\n\n"
        "#Football #FootballNews #Soccer #FootballUpdates #Matchwire #Shorts"
    )

    print("🚀 Uploading to YouTube...")
    print(f"📰 {title}")

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": youtube_title[:100],
                "description": description,
                "tags": [
                    "football",
                    "football news",
                    "football updates",
                    "soccer",
                    "soccer news",
                    "latest football news",
                    "football shorts",
                    "soccer shorts",
                    "Matchwire",
                    "Matchwire football"
                ],
                "categoryId": "17"
            },
            "status": {
                "privacyStatus": "public",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=MediaFileUpload(
            str(VIDEO),
            mimetype="video/mp4",
            resumable=True
        )
    )

    response = request.execute()

    video_id = response["id"]

    print()
    print("=================================")
    print("✅ YOUTUBE UPLOAD SUCCESS")
    print("=================================")
    print()
    print("🆔 Video ID:", video_id)
    print("🌍 Status: PUBLIC")
    print(
        "🔗 https://www.youtube.com/watch?v="
        + video_id
    )
    print()

    return video_id


def main():

    print()
    print("=================================")
    print("MATCHWIRE AUTO YOUTUBE")
    print("=================================")
    print()

    # -------------------------------------------------
    # STEP 1: Check Cloudflare YouTube queue
    # -------------------------------------------------

    try:
        queue = fetch_youtube_queue()
    except Exception as e:
        print(f"⚠️ Could not read YouTube queue: {e}")
        print()
        return

    print(f"📦 YouTube queue: {len(queue)} stories")

    # -------------------------------------------------
    # STEP 2: If queue has stories, process the oldest
    # -------------------------------------------------

    if queue:

        story = queue[0]

        required = ["key", "title", "source", "link"]

        if not all(field in story for field in required):
            print("⚠️ Invalid queue story. Leaving queue unchanged.")
            print()
            return

        story_key = story["key"]

        print()
        print("🆕 Queue story selected!")
        print("📰", story["title"])
        print("🌐", story["source"])
        print("🔗", story["link"])
        print()

        # -------------------------------------------------
        # STEP 3: Local duplicate safety check
        # -------------------------------------------------

        seen = load_seen()

        if story_key in seen:
            print("⏭️ Story already exists in local YouTube history.")
            print("🧹 Removing it from Cloudflare queue.")

            try:
                acknowledge_queue_story(story_key)
            except Exception as e:
                print(f"⚠️ Queue ACK failed: {e}")

            print()
            return

        # -------------------------------------------------
        # STEP 4: Create the EXACT queued story Short
        # -------------------------------------------------

        create_news_short(story)

        # -------------------------------------------------
        # STEP 5: Upload to YouTube
        # -------------------------------------------------

        try:
            video_id = upload_to_youtube(story)

        except HttpError as e:
            error_text = str(e)

            if (
                "uploadLimitExceeded" in error_text
                or "number of videos they may upload" in error_text
            ):
                print()
                print("⚠️ YOUTUBE UPLOAD LIMIT REACHED")
                print("⏸️ Queue story kept for a later run.")
                print("💾 Story NOT marked as uploaded.")
                print("✅ Service will exit cleanly.")
                print()
                return

            raise

        # -------------------------------------------------
        # STEP 6: Mark uploaded locally
        # -------------------------------------------------

        seen.append(story_key)
        seen = seen[-500:]
        save_seen(seen)

        print()
        print("💾 Story marked as uploaded.")

        # -------------------------------------------------
        # STEP 7: ACK Cloudflare queue ONLY after upload
        # -------------------------------------------------

        try:
            acknowledge_queue_story(story_key)
        except Exception as e:
            print(f"⚠️ Upload succeeded but queue ACK failed: {e}")
            print("💡 The next run will detect the local duplicate and ACK it.")
        else:
            print("✅ Queue item acknowledged.")

        print("✅ Duplicate protection enabled.")
        print()

        return

    # -------------------------------------------------
    # STEP 8: No backlog
    # -------------------------------------------------

    print("📭 YouTube queue is empty.")

    # Optional normal live-news mode:
    # only run when there is no Cloudflare backlog.
    try:
        story = fetch_latest_story()
    except Exception as e:
        print(f"⚠️ Could not read latest football story: {e}")
        print()
        return

    if not story:
        print("⚠️ Could not read latest story.")
        print()
        return

    story_key = (
        story["title"].strip().lower()
        + "|"
        + story["link"].strip()
    )

    seen = load_seen()

    if story_key in seen:
        print("⏭️ Latest story already uploaded.")
        print("📰", story["title"])
        print("💾 No YouTube upload needed.")
        print()
        return

    print("🆕 No queue backlog; live story detected.")
    print("📰", story["title"])
    print("🌐", story["source"])
    print("🔗", story["link"])
    print()

    create_news_short()

    try:
        upload_to_youtube(story)

    except HttpError as e:
        error_text = str(e)

        if (
            "uploadLimitExceeded" in error_text
            or "number of videos they may upload" in error_text
        ):
            print()
            print("⚠️ YOUTUBE UPLOAD LIMIT REACHED")
            print("⏸️ Upload skipped for this run.")
            print("💾 Story NOT marked as uploaded.")
            print("✅ Service will exit cleanly.")
            print()
            return

        raise

    seen.append(story_key)
    seen = seen[-500:]
    save_seen(seen)

    print("💾 Story marked as uploaded.")
    print("✅ Duplicate protection enabled.")
    print()


if __name__ == "__main__":
    main()
