---
name: teachable-downloader
description: Downloads videos from online course platforms using yt-dlp. Use this skill whenever the user wants to download or save a video from any online course or learning platform (e.g., "โหลด video course", "save lecture video", "download this course", "ดาวน์โหลดคลิปเรียน"), or when they provide a course platform URL (like teachable.com, hotmart.com, or similar), or an m3u8/HLS stream URL. This skill helps even when the user doesn't know the platform name — if they just say "อยากโหลด video จาก course" or share a URL from a learning site, trigger this skill.
---

# Course Video Downloader

Course platforms (like Teachable) use **Hotmart** as their video player, loading m3u8 URLs dynamically via JavaScript. yt-dlp cannot extract the video directly from a course URL.

## Two Entry Points

### Case A: User provides a course/lecture URL
Run the automation script — it handles everything automatically (no manual steps needed).

### Case B: User provides an m3u8 URL directly (contentplayer.hotmart.com)
Skip to Step 2 immediately.

---

## Step 1: Auto-capture m3u8 URL (Course URL → run script)

Run this command and it will do all 7 steps automatically:

```bash
python3 ~/.claude/skills/teachable-downloader/scripts/get_m3u8.py "<LECTURE_URL>"
```

The script:
1. Exports Chrome session cookies (no login required separately)
2. Opens a browser with the user's login session
3. Navigates to the lecture page
4. Intercepts the m3u8 URL automatically
5. Starts downloading to `~/Downloads/` immediately

Run this as a **background command** and report back to the user.

**Fallback (if script fails):**
> F12 → Network tab → filter `.m3u8` → Play video → Copy URL → ส่งมาให้ผม

---

## Step 2: Download the video (m3u8 URL provided directly)

Only needed if the user provides the m3u8 URL manually (script in Step 1 already handles this):

```bash
cd ~/Downloads && yt-dlp -o "%(title)s.%(ext)s" "<M3U8_URL>"
```

Run as a **background command**.

---

## Checking Progress

If the user asks "still downloading?" or "โหลดเสร็จยัง?", check the background task output and report:
- Current percentage and fragment (e.g., 58% — frag 1244/2120)
- Speed and ETA

---

## Confirm Completion

When done, verify and report the file:
```bash
ls -lh ~/Downloads/*.mp4 | tail -5
```

---

## Important Notes

- **m3u8 URLs expire** in a few hours. If download fails with 403 error → re-run the script to get a fresh URL.
- yt-dlp automatically merges audio/video and fixes the MP4 container.
- Output: `.mp4` in `~/Downloads/`
**macOS setup:**
```bash
brew install yt-dlp
pip3 install playwright --break-system-packages
python3 -m playwright install chromium
```

**Windows setup:**
```powershell
winget install yt-dlp
pip install playwright
python -m playwright install chromium
```
