#!/usr/bin/env python3
"""
Automatically captures m3u8 URL from a Teachable/course lecture.
Works on macOS and Windows.

Steps:
1. Export cookies from Chrome via yt-dlp
2. Launch Playwright browser with cookies injected
3. Navigate to the lecture page
4. Intercept network requests to capture .m3u8 URL
5. Download automatically via yt-dlp

Usage: python3 get_m3u8.py <lecture_url>
"""

import sys
import os
import asyncio
import subprocess
import tempfile
import platform


# ─── Platform helpers ────────────────────────────────────────────────────────

def get_downloads_dir() -> str:
    return os.path.expanduser("~/Downloads")


def get_user_agent() -> str:
    if platform.system() == "Windows":
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )
    return (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )


def get_tmp_path(filename: str) -> str:
    """Cross-platform temp path."""
    if platform.system() == "Windows":
        return os.path.join(os.environ.get("TEMP", "C:\\Temp"), filename)
    return os.path.join("/tmp", filename)


def run_download(m3u8_url: str):
    """Run yt-dlp download in the Downloads folder."""
    downloads = get_downloads_dir()
    os.makedirs(downloads, exist_ok=True)

    if platform.system() == "Windows":
        # Windows: use subprocess to handle paths with spaces
        subprocess.run([
            "yt-dlp", "-o",
            os.path.join(downloads, "%(title)s.%(ext)s"),
            m3u8_url
        ])
    else:
        os.system(f'cd "{downloads}" && yt-dlp -o "%(title)s.%(ext)s" "{m3u8_url}"')


# ─── Cookie export ────────────────────────────────────────────────────────────

def export_cookies(output_file: str) -> bool:
    """Use yt-dlp to export Chrome cookies to a Netscape cookie file."""
    print("Exporting cookies from Chrome...")
    result = subprocess.run(
        [
            "yt-dlp",
            "--cookies-from-browser", "chrome",
            "--cookies", output_file,
            "--skip-download",
            "--quiet",
            "https://www.google.com",
        ],
        capture_output=True, text=True, timeout=30
    )
    return os.path.exists(output_file) and os.path.getsize(output_file) > 0


def parse_netscape_cookies(cookie_file: str) -> list[dict]:
    """Parse Netscape cookie file into Playwright-compatible dicts."""
    cookies = []
    with open(cookie_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 7:
                continue
            domain, _, path, secure, expires, name, value = parts[:7]
            cookies.append({
                "name": name,
                "value": value,
                "domain": domain.lstrip(".") if domain.startswith(".") else domain,
                "path": path,
                "secure": secure.upper() == "TRUE",
                "sameSite": "Lax",
            })
    return cookies


# ─── Main automation ──────────────────────────────────────────────────────────

async def get_m3u8_url(lecture_url: str) -> str | None:
    from playwright.async_api import async_playwright

    m3u8_url = None
    cookie_file = tempfile.mktemp(suffix="_cookies.txt")

    try:
        # Export Chrome cookies
        if not export_cookies(cookie_file):
            print("Warning: Could not export cookies, proceeding without auth")
            cookies = []
        else:
            cookies = parse_netscape_cookies(cookie_file)
            print(f"Loaded {len(cookies)} cookies")

        async with async_playwright() as p:
            print("Launching browser...")
            browser = await p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = await browser.new_context(user_agent=get_user_agent())

            if cookies:
                await context.add_cookies(cookies)

            page = await context.new_page()

            # Intercept requests and look for .m3u8
            async def handle_request(request):
                nonlocal m3u8_url
                if ".m3u8" in request.url and m3u8_url is None:
                    m3u8_url = request.url
                    print("\n✓ Captured m3u8 URL!")

            page.on("request", handle_request)

            print(f"Navigating to: {lecture_url}")
            try:
                await page.goto(lecture_url, wait_until="networkidle", timeout=60000)
            except Exception:
                pass  # networkidle timeout on heavy pages is OK

            # Wait up to 30s, try clicking play every 5s
            print("Waiting for video to load...")
            for i in range(30):
                if m3u8_url:
                    break
                if i % 5 == 0:
                    for frame in page.frames:
                        try:
                            play = await frame.query_selector(
                                'button[aria-label*="play" i], '
                                '.vp-play, .play-btn, [class*="play-button"], '
                                'button[title*="Play"], video'
                            )
                            if play:
                                await play.click()
                        except Exception:
                            pass
                await page.wait_for_timeout(1000)
                print(f"  {i+1}s...", end="\r")

            await browser.close()

    finally:
        if os.path.exists(cookie_file):
            os.unlink(cookie_file)

    return m3u8_url


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 get_m3u8.py <lecture_url>")
        sys.exit(1)

    url = sys.argv[1]
    print(f"Platform: {platform.system()}")
    print(f"Getting m3u8 URL for: {url}\n")

    m3u8 = asyncio.run(get_m3u8_url(url))

    if m3u8:
        print(f"\n{'='*60}")
        print(f"m3u8 URL:\n{m3u8}")
        print(f"{'='*60}")

        # Save URL to temp file for reference
        last_url_file = get_tmp_path("last_m3u8.txt")
        with open(last_url_file, "w") as f:
            f.write(m3u8)
        print(f"\nSaved to {last_url_file}")

        print(f"\nDownloading to {get_downloads_dir()} ...")
        run_download(m3u8)
    else:
        print("\n✗ Could not automatically capture m3u8 URL.")
        print("Fallback: F12 → Network → filter '.m3u8' → Play video → Copy URL")
        sys.exit(1)


if __name__ == "__main__":
    main()
