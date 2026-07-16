# Artispreneur Academy Video Downloader

Downloads all Artispreneur Academy course videos from HeyGen and uploads to Google Drive.

## Videos

- **57 videos** across 8 courses (~1.3 GB, ~8.4 hours)
- Source: `github.com/diamitani/artispreneur-academy` → `lib/courses.ts`

## Prerequisites

```bash
# Install uv if needed
brew install uv

# Clone and set up
git clone <this-repo>
cd academy-video-downloader
uv venv
source .venv/bin/activate
uv pip install playwright
python -m playwright install chromium
```

## Google Drive Setup

```bash
# Configure rclone with your Google Drive
rclone config
# Name the remote: gdrive
# Follow OAuth flow

# Verify
rclone about gdrive:
```

## Usage

```bash
source .venv/bin/activate
python download_intercept.py
```

Videos are saved to `gdrive:Artispreneur_Academy_Videos/course_N/`

## How It Works

HeyGen hosts videos behind CloudFront signed URLs that block direct downloads. This script uses Playwright (headless Chromium) with network route interception — it loads each video's embed page in a real browser and captures the MP4 as it streams to the video player. Then it uploads to Google Drive via rclone and cleans up the local copy.

## Course List

| # | Course | Videos |
|---|--------|--------|
| 1 | How to Brand Yourself as an Artist | 7 |
| 2 | How to Add Music to Collaborative Playlist | 7 |
| 3 | How to Add Songs to Your PRO | 7 |
| 4 | How to Promote Your Own Shows | 7 |
| 5 | How to Copyright Your Music | 7 |
| 6 | How to Create a Music Catalogue | 8 |
| 7 | How to Distribute Your Music | 7 |
| 8 | How to File Business Taxes | 7 |
