#!/bin/bash
# Batch download videos from Google Drive and push to GitHub
# Each batch downloads a few videos, commits them on top of previous,
# then deletes local copies to conserve disk space.
set -e

REPO_DIR="/tmp/academy-video-downloader"
DRIVE_PATH="Artispreneur_Academy_Videos"
BATCH_SIZE=3

cd "$REPO_DIR"

echo "Listing videos from Drive..."
mapfile -t FILES < <(rclone lsf "gdrive:$DRIVE_PATH" --recursive --files-only 2>/dev/null | sort)

TOTAL=${#FILES[@]}
echo "Found $TOTAL videos"
echo ""

# Do a fresh pull in case anything changed
git pull origin main --quiet 2>/dev/null || true

BATCH=1
PROCESSED=0

for ((i=0; i<TOTAL; i+=BATCH_SIZE)); do
    BATCH_FILES=("${FILES[@]:$i:$BATCH_SIZE}")
    echo "=== Batch $BATCH: ${#BATCH_FILES[@]} videos ==="
    
    # Download this batch into videos/
    for FILE in "${BATCH_FILES[@]}"; do
        LOCAL_PATH="$REPO_DIR/videos/$FILE"
        mkdir -p "$(dirname "$LOCAL_PATH")"
        echo "  Downloading: $FILE"
        rclone copyto "gdrive:$DRIVE_PATH/$FILE" "$LOCAL_PATH" --progress 2>&1 | tail -1
        # Stage ONLY this specific file for commit
        git add "videos/$FILE"
    done
    
    # Commit (only staged additions, no deletions) and push
    COMMIT_MSG="Add ${#BATCH_FILES[@]} videos (batch $BATCH, #$((PROCESSED+1))-$((PROCESSED+${#BATCH_FILES[@]}))/$TOTAL)"
    echo "  Committing: $COMMIT_MSG"
    git commit -m "$COMMIT_MSG" --quiet
    
    echo "  Pushing to GitHub..."
    git push origin main --quiet 2>&1 | tail -1
    
    # Delete local files to free space (git history retains them)
    echo "  Freeing disk space..."
    rm -rf videos/
    
    PROCESSED=$((PROCESSED + ${#BATCH_FILES[@]}))
    BATCH=$((BATCH + 1))
    echo "  Done ($PROCESSED/$TOTAL)"
    echo ""
done

echo "ALL DONE: $PROCESSED videos in github.com/diamitani/academy-video-downloader"
echo "Check: https://github.com/diamitani/academy-video-downloader/tree/main/videos"
