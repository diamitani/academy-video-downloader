#!/usr/bin/env python3
"""Download HeyGen videos using Playwright route interception — captures the actual
video file as it streams to the video player."""
import asyncio, json, os, re, subprocess, sys

MANIFEST = "/tmp/academy-downloads/video_manifest.json"
DOWNLOAD_DIR = "/tmp/academy-downloads/videos"
DRIVE_PATH = "Artispreneur_Academy_Videos"

def load_manifest():
    with open(MANIFEST) as f:
        return json.load(f)

async def download_video(browser, video_info, index, total):
    video_id = video_info['video_id']
    module_id = video_info['module_id']
    title = video_info['title']
    
    safe_title = re.sub(r'[^a-zA-Z0-9_-]', '_', title)[:50]
    course_id = module_id.split('-')[0]
    rel_path = f"course_{course_id}/{module_id}_{safe_title}.mp4"
    local_path = os.path.join(DOWNLOAD_DIR, rel_path)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    
    print(f"[{index}/{total}] {title[:70]}")
    
    context = None
    try:
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        )
        page = await context.new_page()
        
        # Intercept MP4 video responses
        video_data = []
        
        async def handle_route(route):
            url = route.request.url
            if '.mp4' in url and 'files' in url and 'heygen' in url:
                print(f"  Intercepting video: {url[:100]}...")
                response = await route.fetch()
                body = await response.body()
                video_data.append(body)
                await route.fulfill(response=response)
            else:
                await route.continue_()
        
        await page.route('**/*', handle_route)
        
        # Navigate and wait for video to start loading
        embed_url = f"https://app.heygen.com/embeds/{video_id}"
        print(f"  Loading embed...")
        await page.goto(embed_url, wait_until='domcontentloaded', timeout=30000)
        
        # Wait for video element and playback
        try:
            await page.wait_for_selector('video', timeout=15000)
            # Click play if needed
            await page.click('video')
            # Wait for video to load data
            await asyncio.sleep(5)
            
            # Try to wait for video to start playing
            await page.evaluate("""
                () => new Promise((resolve) => {
                    const v = document.querySelector('video');
                    if (!v) return resolve('no video');
                    if (v.readyState >= 2) return resolve('loaded');
                    v.addEventListener('loadeddata', () => resolve('loaded'));
                    setTimeout(() => resolve('timeout'), 10000);
                })
            """)
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  Video wait issue: {e}")
        
        await page.close()
        
        if video_data:
            data = video_data[0]
            with open(local_path, 'wb') as f:
                f.write(data)
            size_mb = len(data) / (1024*1024)
            print(f"  Captured: {size_mb:.1f} MB")
            return local_path, rel_path
        else:
            print(f"  No video data captured")
            return None, None
            
    except Exception as e:
        print(f"  Error: {e}")
        return None, None
    finally:
        if context:
            await context.close()

def upload_to_drive(local_path, drive_subpath):
    drive_full = f"gdrive:{DRIVE_PATH}/{drive_subpath}"
    result = subprocess.run(
        ["rclone", "copyto", local_path, drive_full],
        capture_output=True, text=True, timeout=300
    )
    return result.returncode == 0

async def main():
    limit = None
    for i, arg in enumerate(sys.argv):
        if arg == '--limit' and i+1 < len(sys.argv):
            limit = int(sys.argv[i+1])
    
    videos = load_manifest()
    if limit:
        videos = videos[:limit]
    
    print(f"Downloading {len(videos)} videos via route interception...\n")
    
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        success = 0
        
        for i, video in enumerate(videos, 1):
            local_path, rel_path = await download_video(browser, video, i, len(videos))
            
            if local_path:
                print(f"  Uploading...")
                if upload_to_drive(local_path, rel_path):
                    print(f"  ✓ Done")
                    os.remove(local_path)
                    success += 1
                else:
                    print(f"  ⚠ Upload failed, kept local")
            print()
        
        await browser.close()
    
    print(f"COMPLETE: {success}/{len(videos)} succeeded")

if __name__ == '__main__':
    asyncio.run(main())
