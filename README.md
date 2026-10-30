# Matchwire — Football News Automation

Matchwire is a football news collection and publishing project.
It collects football news from RSS sources, filters and organizes
stories, distributes updates through Telegram, and prepares
vertical football-news videos for YouTube Shorts.

## Project Architecture

1. Cloudflare Worker (`worker.js`)
   - Reads configured football news RSS feeds.
   - Filters and deduplicates football stories.
   - Supports the Matchwire news distribution workflow.
   - Provides the authenticated YouTube queue endpoint.

2. Python YouTube automation (`matchwire_auto_youtube.py`)
   - Reads queued stories from the Cloudflare Worker.
   - Validates story fields and checks duplicate history.
   - Sends the selected story to the video generator.
   - Uses OAuth 2.0 credentials for YouTube API access.
   - Uploads the generated MP4 through YouTube Data API.
   - Acknowledges a queue item only after a successful upload.
   - Preserves the current queue item when an upload fails.

3. Video generator (`youtube_news_short.py`)
   - Processes football news stories.
   - Generates a vertical 1080 x 1920 video.
   - Uses a 30-second, 30 FPS output configuration.
   - Produces `matchwire_news_short.mp4`.

## YouTube API Integration

The uploader uses the YouTube Data API v3 `videos.insert` method
with OAuth 2.0 authorization and resumable media upload.

Requested OAuth scopes:
- youtube.upload
- youtube.readonly

The upload code sets video metadata including title, description,
tags, category, and privacy status.

## Queue Safety

- Stories are not acknowledged before successful upload.
- Duplicate story and title history is maintained locally.
- Upload failures leave the current story in the queue.
- Upload-limit errors trigger a cooldown mechanism.

## Main Source Files

- `worker.js` — Cloudflare Worker
- `matchwire_auto_youtube.py` — queue processing and YouTube uploader
- `youtube_news_short.py` — video generation
- `bot.py` — Telegram bot
- `collector.py` — news collection
- `filter.py` — news filtering

## Security

Credentials, OAuth tokens, queue tokens, and runtime state files
must remain private and must never be committed to this repository.

## Project Status

This repository contains the implementation of the Matchwire
automation workflow. Actual successful YouTube publication should
be verified separately using YouTube Studio and upload logs.
