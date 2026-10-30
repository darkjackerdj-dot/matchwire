# YouTube API Usage — Matchwire

## 1. Purpose

Matchwire prepares short-form football news videos and uses the
YouTube Data API to publish them to the project owner's YouTube
channel.

## 2. Data Flow

Football news sources
        |
        v
Cloudflare Worker
        |
        v
Authenticated YouTube queue
        |
        v
matchwire_auto_youtube.py
        |
        v
youtube_news_short.py
        |
        v
MP4 video output
        |
        v
YouTube Data API v3
        |
        v
YouTube channel

## 3. API Usage

The Python uploader uses:
- YouTube Data API v3
- videos.insert
- OAuth 2.0 authorization
- Resumable MP4 media upload

The implementation requests the following scopes:
- https://www.googleapis.com/auth/youtube.upload
- https://www.googleapis.com/auth/youtube.readonly

## 4. Video Processing

The video generator produces a vertical 1080 x 1920 video,
configured for 30 FPS and 30 seconds.

The uploader attaches the story title, source, original article
link, description, tags, and video category.

## 5. Queue and Duplicate Protection

A story is acknowledged in the Cloudflare queue only after
the YouTube upload request succeeds.

The uploader maintains local story and title history to reduce
duplicate publications.

When an upload fails, the current queue item is preserved.
Upload-limit errors activate a cooldown mechanism.

## 6. Demonstration Evidence

The compliance demonstration will show:
1. The project repository and source files.
2. The news queue and selected story.
3. Video generation and the resulting MP4.
4. OAuth authorization without exposing credentials.
5. The YouTube API upload workflow.
6. The actual result in YouTube Studio, if a successful upload
   is available.

No successful upload will be claimed unless it is verified.

## 7. Security and Privacy

OAuth tokens, client secrets, queue tokens, passwords, and
private configuration files are excluded from demonstration
footage and must not be shared publicly.
