from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

VIDEO_FILE = "matchwire_test_short.mp4"

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

credentials = Credentials.from_authorized_user_file(
    "youtube_token.json",
    SCOPES
)

youtube = build("youtube", "v3", credentials=credentials)

body = {
    "snippet": {
        "title": "MATCHWIRE ⚽ Football News | Test Short",
        "description": (
            "⚽ MATCHWIRE — Football News Alerts\n\n"
            "Fast • Reliable • Source-linked\n\n"
            "#Shorts #Football #Matchwire"
        ),
        "tags": [
            "football",
            "football news",
            "Matchwire",
            "Shorts"
        ],
        "categoryId": "17"
    },
    "status": {
        "privacyStatus": "private",
        "selfDeclaredMadeForKids": False
    }
}

media = MediaFileUpload(
    VIDEO_FILE,
    mimetype="video/mp4",
    resumable=True
)

print("🚀 Uploading Matchwire test Short...")

request = youtube.videos().insert(
    part="snippet,status",
    body=body,
    media_body=media
)

response = request.execute()

video_id = response["id"]

print("\n✅ YouTube upload successful!")
print("🆔 Video ID:", video_id)
print("🔒 Status: PRIVATE")
print("📺 Channel: DMR EFX")
print(f"🔗 https://www.youtube.com/watch?v={video_id}")
