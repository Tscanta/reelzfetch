#!/usr/bin/env bash
# Exit immediately if a command fails (-e), treat unset variables as errors (-u),
# and fail a pipeline if any command inside it fails (-o pipefail).
set -euo pipefail

# Find the exact folder where reelfetch.sh lives so we can reliably locate downloader.py.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/downloader.py"

# Print usage instructions and available flags for the user.
print_help() {
  cat <<EOF
ReelFetch - Terminal Instagram Reel Downloader & WAV Converter

Usage:
  ./reelfetch.sh <INSTAGRAM_REEL_URL> [OPTIONS]

Modes (pick one, defaults to --video):
  --video             Download Reel as MP4
  --audio             Extract audio and save as WAV
  --both              Save both MP4 video and WAV audio

Options:
  --browser <name>    Use browser cookies for login-walled Reels (chrome, firefox, edge)
  --out <dir>         Custom output base directory (default: ./downloads)
  --force             Re-download even if Reel ID is already in archive.txt
  -h, --help          Show this help message

Examples:
  ./reelfetch.sh "https://www.instagram.com/reel/ABC123xyz/" --video
  ./reelfetch.sh "https://www.instagram.com/reel/ABC123xyz/" --audio --browser chrome
  ./reelfetch.sh "https://www.instagram.com/reel/ABC123xyz/" --both --out ~/Desktop/reels
EOF
}

# Check whether Python is installed as `python3` or `python` (common on Windows Git Bash).
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "[ERROR] Python is not installed or not in PATH."
  exit 1
fi

# Make sure FFmpeg is installed before starting since WAV conversion depends on it.
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[ERROR] FFmpeg is not installed or not in PATH."
  exit 1
fi

# If the user runs ./reelfetch.sh with no arguments at all, show help and exit.
if [[ $# -eq 0 ]]; then
  print_help
  exit 1
fi

# Default values for command-line arguments and options.
URL=""
MODE="video"
BROWSER=""
OUT_DIR=""
FORCE_FLAG=""

# Loop through all passed arguments ($@) one by one until none remain.
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      print_help
      exit 0
      ;;
    --video)
      # Set mode to video-only (MP4) and move to the next argument.
      MODE="video"
      shift
      ;;
    --audio)
      # Set mode to audio-only (WAV) and move to the next argument.
      MODE="audio"
      shift
      ;;
    --both)
      # Save both MP4 and WAV files.
      MODE="both"
      shift
      ;;
    --browser)
      # Grab the browser name right after --browser and ensure it isn't empty.
      BROWSER="${2:-}"
      if [[ -z "$BROWSER" ]]; then
        echo "[ERROR] --browser requires a browser name (e.g., chrome, firefox)."
        exit 1
      fi
      # Shift twice because we consumed both `--browser` and its value.
      shift 2
      ;;
    --out)
      # Grab the custom output folder path and ensure a value was provided.
      OUT_DIR="${2:-}"
      if [[ -z "$OUT_DIR" ]]; then
        echo "[ERROR] --out requires a directory path."
        exit 1
      fi
      shift 2
      ;;
    --force)
      # Pass --force to Python so previously archived Reels get re-downloaded.
      FORCE_FLAG="--force"
      shift
      ;;
    -*)
      # Catch any unknown flag starting with a dash.
      echo "[ERROR] Unknown option: $1"
      print_help
      exit 1
      ;;
    *)
      # Treat the first non-flag argument as the Instagram Reel URL.
      if [[ -z "$URL" ]]; then
        URL="$1"
      else
        echo "[ERROR] Unexpected extra argument: $1"
        exit 1
      fi
      shift
      ;;
  esac
done

# Ensure a URL was actually provided somewhere in the arguments.
if [[ -z "$URL" ]]; then
  echo "[ERROR] Missing Instagram Reel URL."
  print_help
  exit 1
fi

# Build the final Python command array safely (handles spaces in paths or URLs).
CMD=("$PYTHON_BIN" "$PYTHON_SCRIPT" "$URL" "--mode" "$MODE")
[[ -n "$BROWSER" ]] && CMD+=("--browser" "$BROWSER")
[[ -n "$OUT_DIR" ]] && CMD+=("--out-dir" "$OUT_DIR")
[[ -n "$FORCE_FLAG" ]] && CMD+=("$FORCE_FLAG")

# Execute downloader.py with the assembled arguments.
"${CMD[@]}"