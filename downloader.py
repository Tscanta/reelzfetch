#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import yt_dlp
from yt_dlp.utils import DownloadError


# Locate the project root so config/, downloads/, and logs/ resolve reliably from anywhere.
BASE_DIR = Path(__file__).resolve().parent
LOG_FILE = BASE_DIR / "logs" / "download.log"
ARCHIVE_FILE = BASE_DIR / "logs" / "archive.txt"
CONFIG_FILE = BASE_DIR / "config.json"


def load_default_out_dir() -> Path:
    """Read custom default download folder from config.json, or fall back to ./downloads."""
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            saved = data.get("default_out_dir", "").strip()
            if saved:
                return Path(os.path.expanduser(saved)).resolve()
        except (OSError, json.JSONDecodeError):
            pass
    return (BASE_DIR / "downloads").resolve()


def save_default_out_dir(custom_dir: str) -> Path:
    """Persist a user-chosen default download folder into config.json."""
    target = Path(os.path.expanduser(custom_dir.strip())).resolve()
    target.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps({"default_out_dir": str(target)}, indent=2),
        encoding="utf-8",
    )
    return target


def make_clickable_path(path: Path, label: str | None = None) -> str:
    """Wrap a local Path in an OSC 8 file:// hyperlink supported by Windows Terminal, VS Code, and Git Bash."""
    resolved = path.resolve()
    display_text = label if label is not None else str(resolved)
    # Respect NO_COLOR / dumb terminals by falling back to plain text.
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return display_text
    uri = resolved.as_uri()
    return f"\033]8;;{uri}\033\\{display_text}\033]8;;\033\\"


def write_log(level: str, message: str) -> None:
    """Append a timestamped UTF-8 entry to logs/download.log without crashing on special chars."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            f.write(f"[{timestamp}] [{level}] {message}\n")
    except OSError as exc:
        print(f"  [WARN   ] Could not write to log file: {exc}")


def print_status(tag: str, message: str) -> None:
    """Print a clean, aligned status line to the terminal and record it in the log."""
    write_log(tag, message)
    try:
        print(f"  [{tag:<7}] {message}")
    except UnicodeEncodeError:
        safe_msg = message.encode("ascii", errors="replace").decode("ascii")
        print(f"  [{tag:<7}] {safe_msg}")


def format_size(num_bytes: int) -> str:
    """Convert raw bytes into a human-readable KB/MB string."""
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} TB"


def validate_instagram_url(url: str) -> bool:
    """Check that the input looks like an Instagram Reel, Post, or TV URL."""
    pattern = r"^https?://(www\.)?instagram\.com/(reel|reels|p|tv)/[A-Za-z0-9_-]+/?(?:\?.*)?$"
    return bool(re.match(pattern, url.strip()))


def download_progress_hook(status: dict) -> None:
    """Render a single-line live download progress bar instead of raw yt-dlp noise."""
    state = status.get("status")
    if state == "downloading":
        percent = status.get("_percent_str", "  0.0%").strip()
        speed = status.get("_speed_str", "N/A").strip()
        eta = status.get("_eta_str", "--:--").strip()
        line = f"\r  [FETCH  ] Downloading stream... {percent} | Speed: {speed} | ETA: {eta}   "
        try:
            sys.stdout.write(line)
        except UnicodeEncodeError:
            sys.stdout.write(line.encode("ascii", errors="replace").decode("ascii"))
        sys.stdout.flush()
    elif state == "finished":
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
        print_status("FETCH", "Stream download complete. Finalizing container...")


def download_video(url: str, video_dir: Path, browser: str | None = None, force: bool = False) -> Path:
    """Download the Reel/post video as MP4 with detailed error reporting."""
    try:
        video_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(f"Cannot create video folder '{video_dir}': {exc}") from exc

    output_template = str(video_dir / "%(uploader)s_%(id)s.%(ext)s")

    ydl_opts = {
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "merge_output_format": "mp4",
        "outtmpl": output_template,
        "sleep_requests": 2,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "progress_hooks": [download_progress_hook],
        "encoding": "utf-8",
    }

    if not force:
        ydl_opts["download_archive"] = str(ARCHIVE_FILE)

    if browser:
        ydl_opts["cookiesfrombrowser"] = (browser,)

    print_status("INFO", "Connecting to Instagram and inspecting media metadata...")

    info = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise RuntimeError(
                    "Instagram returned no media info. The post may be private/restricted—try --browser chrome."
                )

            title = (info.get("title") or "Untitled").strip().splitlines()[0][:55]
            uploader = info.get("uploader") or "unknown"
            filepath = Path(ydl.prepare_filename(info)).with_suffix(".mp4")

            print_status("FOUND", f"Creator: @{uploader} | Title: \"{title}\"")
    except DownloadError as exc:
        raise RuntimeError(
            f"Download error: {exc}. Try --browser chrome if login is required, "
            "or update yt-dlp with 'pip install -U yt-dlp'."
        ) from exc

    if not filepath.exists():
        matches = list(video_dir.glob(f"*_{info.get('id', '')}.*")) if info else []
        if matches:
            filepath = matches[0]
        else:
            raise FileNotFoundError(
                f"Expected MP4 not found at '{filepath}'. If already archived, pass --force to re-download."
            )

    if filepath.stat().st_size == 0:
        filepath.unlink(missing_ok=True)
        raise RuntimeError(f"Downloaded file '{filepath.name}' is empty (0 bytes) and was removed.")

    size_str = format_size(filepath.stat().st_size)
    print_status("SAVED", f"MP4 ready -> {filepath.name} ({size_str})")
    return filepath


def convert_to_wav(mp4_path: Path, audio_dir: Path) -> Path:
    """Convert the MP4 audio track to 16-bit PCM stereo WAV (44.1 kHz) via FFmpeg."""
    if not mp4_path.exists():
        raise FileNotFoundError(f"Source video file missing for audio conversion: '{mp4_path}'")

    try:
        audio_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(f"Cannot create audio folder '{audio_dir}': {exc}") from exc

    wav_path = audio_dir / f"{mp4_path.stem}.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(mp4_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(wav_path),
    ]

    print_status("CONVERT", "Extracting audio track and encoding 16-bit WAV (44.1 kHz)...")

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("FFmpeg not found. Verify FFmpeg is installed and available in PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        wav_path.unlink(missing_ok=True)
        raise RuntimeError("FFmpeg timed out while converting audio to WAV.") from exc

    if result.returncode != 0 or not wav_path.exists() or wav_path.stat().st_size == 0:
        wav_path.unlink(missing_ok=True)
        write_log("FFMPEG_STDERR", result.stderr or "(empty stderr)")
        raise RuntimeError("FFmpeg conversion failed. Check logs/download.log for details.")

    size_str = format_size(wav_path.stat().st_size)
    print_status("SAVED", f"WAV ready -> {wav_path.name} ({size_str})")
    return wav_path


def main() -> int:
    parser = argparse.ArgumentParser(description="ReelFetch Python Media Engine")
    parser.add_argument("url", nargs="?", help="Instagram Reel or Post URL")
    parser.add_argument("--mode", choices=["video", "audio", "both"], default="video")
    parser.add_argument("--out-dir", help="One-time custom base output directory")
    parser.add_argument("--set-dir", help="Save a new permanent default download directory")
    parser.add_argument("--browser", help="Browser name for cookies (e.g., chrome, firefox, edge)")
    parser.add_argument("--force", action="store_true", help="Re-download even if in archive.txt")
    args = parser.parse_args()

    # Handle --set-dir (save persistent custom download folder)
    if args.set_dir:
        try:
            saved_dir = save_default_out_dir(args.set_dir)
            print("============================================================")
            print(f"  Default download folder updated!")
            print(f"  -> Location : {make_clickable_path(saved_dir)}")
            print("============================================================")
            if not args.url:
                return 0
        except OSError as exc:
            print_status("FAILED", f"Could not save custom directory '{args.set_dir}': {exc}")
            return 1

    if not args.url:
        print_status("ERROR", "Missing Instagram Reel URL.")
        return 1

    total_steps = 2 if args.mode == "video" else 3
    base_out = Path(os.path.expanduser(args.out_dir)).resolve() if args.out_dir else load_default_out_dir()
    video_dir = base_out / "videos"
    audio_dir = base_out / "audio"

    print("------------------------------------------------------------")
    print(f"  Target URL : {args.url}")
    print(f"  Mode       : {args.mode.upper()}")
    print(f"  Save Folder: {make_clickable_path(base_out)}  (Ctrl+Click to open)")
    if args.browser:
        print(f"  Cookies    : {args.browser}")
    print("------------------------------------------------------------\n")

    # Step 1: Validate URL
    print(f"[Step 1/{total_steps}] Validating URL")
    if not validate_instagram_url(args.url):
        print_status("ERROR", "Invalid Instagram URL format. Expected https://www.instagram.com/reel/<id>/")
        return 1
    print_status("OK", "Valid Instagram link detected.\n")

    try:
        # Step 2: Download Video
        print(f"[Step 2/{total_steps}] Fetching Video Stream")
        mp4_path = download_video(args.url, video_dir, browser=args.browser, force=args.force)
        print("")

        saved_files: list[tuple[str, Path]] = []
        if args.mode in ("video", "both"):
            saved_files.append(("MP4 Video", mp4_path))

        # Step 3: Audio Extraction (if requested)
        if args.mode in ("audio", "both"):
            print(f"[Step 3/{total_steps}] Converting Audio to WAV")
            wav_path = convert_to_wav(mp4_path, audio_dir)
            saved_files.append(("WAV Audio", wav_path))

            if args.mode == "audio" and mp4_path.exists():
                try:
                    mp4_path.unlink()
                    print_status("CLEANUP", f"Removed temporary MP4 ({mp4_path.name})")
                except OSError as exc:
                    print_status("WARN", f"Could not remove temporary MP4 '{mp4_path.name}': {exc}")
            print("")

        print("============================================================")
        print("  DONE! All tasks completed successfully.")
        for label, path in saved_files:
            print(f"  -> {label:<10}: {make_clickable_path(path)}")
            print(f"     Folder    : {make_clickable_path(path.parent)}")
        print("  (Tip: Ctrl+Click any path above to open it directly)")
        print("============================================================")
        return 0

    except KeyboardInterrupt:
        print("\n============================================================")
        print_status("CANCELLED", "Operation interrupted by user (Ctrl+C).")
        print("============================================================")
        return 130

    except Exception as exc:
        print("")
        print("============================================================")
        print_status("FAILED", str(exc))
        print(f"  -> Full log : {make_clickable_path(LOG_FILE)}")
        print("============================================================")
        return 1


if __name__ == "__main__":
    sys.exit(main())