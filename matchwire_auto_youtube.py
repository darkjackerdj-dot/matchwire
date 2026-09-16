import subprocess
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials


# ==========================================
# MATCHWIRE AUTO YOUTUBE
# ==========================================

VIDEO = Path("matchwire_news_short.mp4")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def create_news_short():
    print("🎬 Creating latest Matchwire Short...")

    subprocess.run(
        ["python", "youtube_news_short.py"],
        check=True
    )

    print("✅ Short created!")


def upload_to_youtube():

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

    print("🚀 Uploading to YouTube...")

    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": "⚽ Matchwire Football News Update",
                "description": (
                    "⚽ Matchwire Football News\n\n"
                    "Fast, reliable and source-linked "
                    "football updates.\n\n"
                    "Follow Matchwire:\n"
                    "@matchwirenews"
                ),
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
                "privacyStatus": "private",
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
    print("🔒 Status: PRIVATE")
    print(
        "🔗 https://www.youtube.com/watch?v="
        + video_id
    )
    print()


def main():

    print()
    print("=================================")
    print("MATCHWIRE AUTO YOUTUBE")
    print("=================================")
    print()

    create_news_short()

    upload_to_youtube()


if __name__ == "__main__":
    main()
