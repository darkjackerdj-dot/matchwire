# Matchwire — YouTube API Compliance Screencast

Target duration: approximately 4–6 minutes.

## Scene 1 — Introduction
Introduce Matchwire and explain its football-news automation purpose.

## Scene 2 — Source code
Show worker.js and explain news collection, filtering, and queue flow.

## Scene 3 — Queue processing
Show matchwire_auto_youtube.py and explain story validation,
duplicate protection, and queue acknowledgement.

## Scene 4 — Video generation
Show youtube_news_short.py and the generated MP4 video.
Explain the vertical video format and duration.

## Scene 5 — YouTube API integration
Show the OAuth 2.0 flow and videos.insert implementation.
Do not expose tokens, secrets, passwords, or private keys.

## Scene 6 — Final result
If an actual successful upload exists, show the corresponding
video in YouTube Studio and its real status.

If upload is blocked by a quota or API limit, show the genuine
error and explain that publication is pending. Do not simulate
or claim a successful upload.

## Closing
Summarize the workflow and explain that queue acknowledgement
happens only after a successful upload.
