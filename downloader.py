#!/usr/bin/env python3
import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path
import yt_dlp


# Figure out where this script lives so all relative paths work
# no matter which folder you run the command from.
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_VIDEO_DIR = BASE_DIR / "downloads" / "videos"
DEFAULT_AUDIO_DIR = BASE_DIR / "downloads" / "audio"
LOG_FILE = BASE_DIR / "logs" / "download.log"
ARCHIVE_FILE = BASE_DIR / "logs" / "archive.txt"


def log_message(level: str, message: str) -> None:
    """Write a timestamped status message to the log file and print it to the terminal."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{level}] {message}\n"

    # Open in append mode ('a') so past logs aren't overwritten.
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

    print(f"[{level}] {message}")


def validate_instagram_url(url: str) -> bool:
    """Check that the input looks like an Instagram Reel/post/TV link before calling yt-dlp."""
    pattern = r"^https?://(www\.)?instagram\.com/(reel|reels|p|tv)/[A-Za-z0-9_-]+/?"
    return bool(re.match(pattern, url.strip()))


def download_video(url: str, video_dir: Path, browser: str | None = None, force: bool = False) -> Path:
    """Download the Instagram Reel as an MP4 file using yt-dlp."""
    # Create the videos folder if it doesn't exist yet.
    video_dir.mkdir(parents=True, exist_ok=True)

    # Name files like "<uploader>_<shortcode>.mp4" so they stay organized and unique.
    output_template = str(video_dir / "%(uploader)s_%(id)s.%(ext)s")

    ydl_opts = {
        # Prefer MP4 video + M4A audio, falling back to any combined MP4 or best available stream.
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        # Pause briefly between requests to avoid hitting Instagram too fast.
        "sleep_requests": 2,
        "quiet": False,
        "no_warnings": True,
    }

    # Skip Reels already recorded in archive.txt unless the user passed --force.
    if not force:
        ydl_opts["download_archive"] = str(ARCHIVE_FILE)

    # Pass browser cookies when needed for Reels behind a login prompt.
    if browser:
        ydl_opts["cookiesfrombrowser"] = (browser,)

    log_message("INFO", f"Fetching Reel metadata & video: {url}")

    # Run yt-dlp to extract media info and download the file.
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            raise RuntimeError("Extraction returned no data. Try passing --browser chrome (or firefox/edge).")
        filepath = Path(ydl.prepare_filename(info)).with_suffix(".mp4")

    if not filepath.exists():
        raise FileNotFoundError(f"Expected MP4 file not found at {filepath}")

    log_message("SUCCESS", f"Saved MP4: {filepath}")
    return filepath


def convert_to_wav(mp4_path: Path, audio_dir: Path) -> Path:
    """Extract audio from an MP4 file and convert it to a standard WAV file using FFmpeg."""
    audio_dir.mkdir(parents=True, exist_ok=True)
    wav_path = audio_dir / f"{mp4_path.stem}.wav"

    # Build the FFmpeg command to strip video (-vn) and output 16-bit PCM stereo WAV at 44.1 kHz.
    cmd = [
        "ffmpeg",
        "-y",                  # Overwrite existing WAV file without asking
        "-i", str(mp4_path),   # Input MP4 file
        "-vn",                 # Drop the video track
        "-acodec", "pcm_s16le",# Uncompressed 16-bit WAV audio codec
        "-ar", "44100",        # 44,100 Hz sample rate (CD quality)
        "-ac", "2",            # 2 channels (stereo)
        str(wav_path),         # Output WAV path
    ]

    log_message("INFO", f"Converting to WAV: {wav_path.name}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0 or not wav_path.exists():
        raise RuntimeError(f"FFmpeg conversion failed:\n{result.stderr}")

    log_message("SUCCESS", f"Saved WAV: {wav_path}")
    return wav_path


def main() -> int:
    """Parse command-line arguments and run the requested download/conversion workflow."""
    parser = argparse.ArgumentParser(description="ReelFetch Python Media Engine")
    parser.add_argument("url", help="Instagram Reel URL")
    parser.add_argument("--mode", choices=["video", "audio", "both"], default="video")
    parser.add_argument("--out-dir", help="Custom base output directory")
    parser.add_argument("--browser", help="Browser name for cookies (e.g., chrome, firefox, edge)")
    parser.add_argument("--force", action="store_true", help="Re-download even if in archive.txt")
    args = parser.parse_args()

    # Stop early if the URL format doesn't match an Instagram link.
    if not validate_instagram_url(args.url):
        log_message("ERROR", f"Invalid Instagram Reel URL: {args.url}")
        return 1

    # Use a custom output folder if provided, otherwise fall back to ReelFetch/downloads.
    base_out = Path(args.out_dir).resolve() if args.out_dir else BASE_DIR / "downloads"
    video_dir = base_out / "videos"
    audio_dir = base_out / "audio"

    try:
        # Always download the MP4 first so we have a local source file to extract audio from.
        mp4_path = download_video(args.url, video_dir, browser=args.browser, force=args.force)

        # Convert to WAV when the user wants audio only or both formats.
        if args.mode in ("audio", "both"):
            convert_to_wav(mp4_path, audio_dir)

        # If the user only wanted audio (--mode audio), delete the temporary MP4 afterward.
        if args.mode == "audio" and mp4_path.exists():
            mp4_path.unlink()
            log_message("INFO", f"Cleaned up temporary MP4: {mp4_path.name}")

        return 0
    except Exception as exc:
        log_message("ERROR", str(exc))
        return 1


if __name__ == "__main__":
    # Exit with the status code returned by main() (0 = success, 1 = error).
    sys.exit(main())