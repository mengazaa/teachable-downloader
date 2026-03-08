# Teachable Downloader — Claude Code Skill

Download videos from online course platforms (Teachable, Hotmart, etc.) with a single command.

## What it does

1. Exports Chrome session cookies automatically
2. Opens browser with your login session
3. Navigates to the lecture page
4. Captures the m3u8 video stream URL
5. Downloads to `~/Downloads/`

## Install Dependencies

**macOS:**
```bash
brew install yt-dlp
pip3 install playwright --break-system-packages
python3 -m playwright install chromium
```

**Windows:**
```powershell
winget install yt-dlp
pip install playwright
python -m playwright install chromium
```

## Install as Claude Code Skill

Copy to your Claude Code skills directory:
```bash
mkdir -p ~/.claude/skills/teachable-downloader/scripts
cp SKILL.md ~/.claude/skills/teachable-downloader/
cp scripts/get_m3u8.py ~/.claude/skills/teachable-downloader/scripts/
```

## Usage

Just tell Claude Code:
- "โหลดวิดีโอจาก course นี้ให้หน่อย [URL]"
- "download this lecture for me [URL]"
- "save this course video to my computer"

## License

MIT
