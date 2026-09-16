import json
import subprocess
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials


VIDEO = Path("matchwire_news_short.mp4")
SEEN_FILE = Path("youtube_seen.json")
METADATA_FILE = Path("matchwire_latest.json")

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


def create_news_short():
    print("🎬 Creating latest Matchwire Short...")

    subprocess.run(
        ["python", "youtube_news_short.py"],
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
    Fetch the latest story metadata without rendering the video.
    """
    print("🔎 Checking latest football news...")

    subprocess.run(
        ["python", "youtube_news_short.py", "--metadata-only"],
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

    youtube_title = (
        f"Matchwire Football News: {title}"
    )

    description = (
        "⚽ Matchwire Football News\n\n"
        f"{title}\n\n"
        f"Source: {source}\n"
        f"Original story: {link}\n\n"
        "Follow Matchwire:\n"
        "@matchwirenews\n\n"
        "#football #soccer #footballnews #Matchwire"
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
                    "soccer",
                    "football news",
                    "football updates",
                    "Matchwire"
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
    # STEP 1: Check latest RSS story
    # -------------------------------------------------

    story = fetch_latest_story()

    if not story:
        print("⚠️ Could not read latest story.")
        print()
        return

    story_key = (
        story["title"].strip().lower()
        + "|"
        + story["link"].strip()
    )

    # -------------------------------------------------
    # STEP 2: Check duplicate BEFORE uploading
    # -------------------------------------------------

    seen = load_seen()

    if story_key in seen:
        print("⏭️ Latest story already uploaded.")
        print("📰", story["title"])
        print("💾 No YouTube upload needed.")
        print()
        return

    # -------------------------------------------------
    # STEP 3: New story detected
    # -------------------------------------------------

    print("🆕 New story detected!")
    print("📰", story["title"])
    print("🌐", story["source"])
    print("🔗", story["link"])
    print()

    # -------------------------------------------------
    # STEP 4: Create Short ONLY for new story
    # -------------------------------------------------

    create_news_short()

    # -------------------------------------------------
    # STEP 5: Upload to YouTube
    # -------------------------------------------------

    upload_to_youtube(story)

    # -------------------------------------------------
    # STEP 6: Mark as uploaded
    # -------------------------------------------------

    seen.append(story_key)

    # Keep latest 500 records
    seen = seen[-500:]

    save_seen(seen)

    print("💾 Story marked as uploaded.")
    print("✅ Duplicate protection enabled.")
    print()


if __name__ == "__main__":
    main()
