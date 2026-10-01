from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

flow = InstalledAppFlow.from_client_secrets_file(
    "youtube_client_secret.json",
    SCOPES,
)

credentials = flow.run_local_server(
    port=0,
    access_type="offline",
    prompt="consent",
)

with open("youtube_token.json", "w") as f:
    f.write(credentials.to_json())

print("✅ Fresh YouTube OAuth token created: youtube_token.json")
