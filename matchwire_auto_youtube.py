import json
import re
import time
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
TITLE_SEEN_FILE = Path("youtube_seen_titles.json")
METADATA_FILE = Path("matchwire_latest.json")

QUEUE_URL = "https://matchwire.darkjackerdj.workers.dev/youtube-queue"
QUEUE_TOKEN_FILE = Path(".youtube_queue_token")
QUEUE_STORY_FILE = Path("matchwire_queue_story.json")

COOLDOWN_FILE = Path(".youtube_upload_cooldown.json")
COOLDOWN_SECONDS = 24 * 60 * 60


def check_upload_cooldown():
    if not COOLDOWN_FILE.exists():
        return False

    try:
        data = json.loads(COOLDOWN_FILE.read_text())
        retry_at = float(data["retry_at"])
    except Exception:
        print("WARNING: Invalid cooldown marker; preserving it.")
        print("Please inspect", COOLDOWN_FILE)
        return True

    remaining = retry_at - time.time()

    if remaining > 0:
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        print("YouTube upload cooldown is active.")
        print(f"Retry in approximately {hours}h {minutes}m.")
        print("Queue remains unchanged; skipping video rendering.")
        return True

    COOLDOWN_FILE.unlink()
    print("Upload cooldown expired; attempting upload again.")
    return False


def start_upload_cooldown():
    data = {
        "retry_at": time.time() + COOLDOWN_SECONDS,
        "reason": "YouTube upload limit error",
    }
    temp = COOLDOWN_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2))
    temp.replace(COOLDOWN_FILE)
    print("Cooldown saved for 24 hours.")
    print("The queued story has not been acknowledged.")

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


def normalize_story_title(title):
    title = title.lower()
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return " ".join(title.split())


def load_seen_titles():
    if not TITLE_SEEN_FILE.exists():
        return []

    try:
        data = json.loads(TITLE_SEEN_FILE.read_text())
        return data if isinstance(data, list) else []
    except Exception:
        print("WARNING: Could not read title history; stopping safely.")
        raise


def save_seen_titles(titles):
    temp = TITLE_SEEN_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(titles, indent=2))
    temp.replace(TITLE_SEEN_FILE)


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

    while check_upload_cooldown():
        print("Cooldown active; checking again in 5 minutes.")
        time.sleep(300)

    print()
    print("=================================")
    print("MATCHWIRE AUTO YOUTUBE")
    print("=================================")
    print()

    # Keep processing queued stories until:
    # - the queue is empty, or
    # - an upload/error stops the process.
    while True:

        try:
            queue = fetch_youtube_queue()
        except Exception as e:
            print(f"⚠️ Could not read YouTube queue: {e}")
            return

        print(f"📦 YouTube queue: {len(queue)} stories")

        if not queue:
            print("📭 Queue empty. Checking again in 60 seconds.")
            time.sleep(60)
            continue

        story = queue[0]

        required = ["key", "title", "source", "link"]

        if not all(field in story for field in required):
            print("⚠️ Invalid queue story. Leaving queue unchanged.")
            return

        story_key = story["key"]

        print()
        print("🆕 Queue story selected!")
        print("📰", story["title"])
        print("🌐", story["source"])
        print("🔗", story["link"])
        print()

        # Local duplicate safety
        seen = load_seen()

        if story_key in seen:
            print("⏭️ Already uploaded locally.")
            print("🧹 Removing stale queue item.")

            try:
                acknowledge_queue_story(story_key)
            except Exception as e:
                print(f"⚠️ Queue ACK failed: {e}")
                return

            continue

        # Prevent duplicate headlines even when article URLs/keys differ.
        normalized_title = normalize_story_title(story["title"])

        try:
            seen_titles = load_seen_titles()
        except Exception:
            print("Cannot verify title history; refusing upload.")
            return

        if normalized_title in seen_titles:
            print("⏭️ Duplicate headline already uploaded; skipping.")
            try:
                acknowledge_queue_story(story_key)
            except Exception as e:
                print(f"⚠️ Duplicate queue ACK failed: {e}")
                return
            continue

        # Render exact queued story
        create_news_short(story)

        # Upload
        try:
            upload_to_youtube(story)

        except HttpError as e:
            error_text = str(e)

            print(f"ORIGINAL YOUTUBE API ERROR: {e}", flush=True)
            if (
                "uploadLimitExceeded" in error_text
                or "number of videos they may upload" in error_text
                or "rateLimitExceeded" in error_text
                or "Video Uploads per day" in error_text
                or "Quota exceeded for quota metric" in error_text
            ):
                print()
                print("⚠️ YOUTUBE UPLOAD QUOTA/LIMIT REACHED")
                start_upload_cooldown()
                print("⏸️ Queue processing stopped.")
                print("💾 Current story remains in queue.")
                print("✅ Service will exit cleanly.")
                print()
                return

            raise

        except Exception as e:
            print()
            print(f"❌ YouTube upload failed: {e}")
            print("💾 Current story remains in queue.")
            print("✅ Service will exit cleanly.")
            print()
            return

        # Mark local history only after successful upload
        seen.append(story_key)
        seen = seen[-500:]
        save_seen(seen)

        # Record headline only after a successful YouTube upload.
        seen_titles = load_seen_titles()
        if normalized_title not in seen_titles:
            seen_titles.append(normalized_title)
            save_seen_titles(seen_titles)

        print("💾 Story and headline marked as uploaded.")

        # ACK Cloudflare only after successful upload
        try:
            acknowledge_queue_story(story_key)
        except Exception as e:
            print(f"⚠️ Upload succeeded but queue ACK failed: {e}")
            print("⏸️ Stopping to avoid duplicate processing.")
            return

        print("✅ Queue item acknowledged.")
        print("✅ Duplicate protection enabled.")
        print()

        print("➡️ Upload complete. Checking the next queued story.")
        print()
        continue


if __name__ == "__main__":
    main()
