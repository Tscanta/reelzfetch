#!/usr/bin/env bash
# Exit immediately if a command fails (-e), treat unset variables as errors (-u),
# and fail a pipeline if any command inside it fails (-o pipefail).
set -euo pipefail

# Locate the folder containing this script so downloader.py is always found reliably.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/downloader.py"

# Print the ASCII title banner.
print_banner() {
  cat <<'EOF'
____  _____ _____ _     _____ _____ _____ _____ ____ _   _
 |  _ \| ____| ____| |   |__  /|  ___| ____|_   _/ ___| | | |
 | |_) |  _| |  _| | |     / / | |_  |  _|   | || |   | |_| |
 |  _ <| |___| |___| |___ / /_ |  _| | |___  | || |___|  _  |
 |_| \_\_____|_____|_____/____||_|   |_____| |_| \____|_| |_|
        Terminal Instagram Reel Downloader & WAV Converter
EOF
}

# Print the ASCII banner along with clear usage instructions and examples.
print_usage() {
  print_banner
  cat <<'EOF'

HOW TO RUN IT:
  ./reelfetch.sh "<INSTAGRAM_REEL_URL>" [MODE] [OPTIONS]

MODES (defaults to --video):
  --video             Download the Reel as an MP4 video
  --audio             Extract audio and save as a WAV file
  --both              Save both MP4 video and WAV audio

OPTIONS:
  --browser <name>    Use browser cookies for login-walled Reels (chrome, firefox, edge)
  --out <dir>         Custom output base directory (default: ./downloads)
  --force             Re-download even if the Reel ID is already in logs/archive.txt
  -h, --help          Display this banner and usage guide

EXAMPLES:
  ./reelfetch.sh "https://www.instagram.com/reel/ABC123xyz/" --video
  ./reelfetch.sh "https://www.instagram.com/reel/ABC123xyz/" --audio --browser chrome
  ./reelfetch.sh "https://www.instagram.com/reel/ABC123xyz/" --both --out ./my_reels

EOF
}

# Prefer Windows Python 3.11 if present, otherwise fall back to python3 / python.
WIN_PYTHON="/c/Users/TSHEDUP/AppData/Local/Programs/Python/Python311/python.exe"
if [[ -x "$WIN_PYTHON" ]]; then
  PYTHON_BIN="$WIN_PYTHON"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "[ERROR] Python is not installed or not in PATH."
  exit 1
fi

# Verify FFmpeg is available before running.
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[ERROR] FFmpeg is not installed or not in PATH."
  exit 1
fi

# Show banner + instructions if no arguments are passed.
if [[ $# -eq 0 ]]; then
  print_usage
  exit 0
fi

URL=""
MODE="video"
BROWSER=""
OUT_DIR=""
FORCE_FLAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help)
      print_usage
      exit 0
      ;;
    --video)
      MODE="video"
      shift
      ;;
    --audio)
      MODE="audio"
      shift
      ;;
    --both)
      MODE="both"
      shift
      ;;
    --browser)
      BROWSER="${2:-}"
      if [[ -z "$BROWSER" ]]; then
        echo "[ERROR] --browser requires a browser name (e.g., chrome, firefox)."
        exit 1
      fi
      shift 2
      ;;
    --out)
      OUT_DIR="${2:-}"
      if [[ -z "$OUT_DIR" ]]; then
        echo "[ERROR] --out requires a directory path."
        exit 1
      fi
      shift 2
      ;;
    --force)
      FORCE_FLAG="--force"
      shift
      ;;
    -*)
      echo "[ERROR] Unknown option: $1"
      echo "Run './reelfetch.sh --help' to see valid options."
      exit 1
      ;;
    *)
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

if [[ -z "$URL" ]]; then
  echo "[ERROR] Missing Instagram Reel URL."
  echo "Run './reelfetch.sh --help' for usage instructions."
  exit 1
fi

# Display the banner cleanly at the start of an active download/conversion run.
print_banner
echo ""

CMD=("$PYTHON_BIN" "$PYTHON_SCRIPT" "$URL" "--mode" "$MODE")
[[ -n "$BROWSER" ]] && CMD+=("--browser" "$BROWSER")
[[ -n "$OUT_DIR" ]] && CMD+=("--out-dir" "$OUT_DIR")
[[ -n "$FORCE_FLAG" ]] && CMD+=("$FORCE_FLAG")

"${CMD[@]}"