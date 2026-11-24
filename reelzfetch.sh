#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/downloader.py"
CONFIG_FILE="$SCRIPT_DIR/config.json"

get_current_out_dir() {
  if [[ -f "$CONFIG_FILE" ]]; then
    "$PYTHON_BIN" -c 'import json, pathlib; p = pathlib.Path(r"'"$CONFIG_FILE"'"); print(json.loads(p.read_text(encoding="utf-8")).get("default_out_dir", ""))' 2>/dev/null || echo "$SCRIPT_DIR/downloads"
  else
    echo "$SCRIPT_DIR/downloads"
  fi
}

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

print_usage() {
  print_banner
  local current_dir
  current_dir="$(get_current_out_dir)"
  cat <<EOF

CURRENT DOWNLOAD FOLDER:
  $current_dir

HOW TO RUN IT:
  reelzfetch "<INSTAGRAM_REEL_URL>" [MODE] [OPTIONS]

MODES (defaults to --video):
  --video             Download the Reel as an MP4 video
  --audio             Extract audio and save as a WAV file
  --both              Save both MP4 video and WAV audio

OPTIONS:
  --out <dir>         Save to a custom folder for this download only
  --set-dir <dir>     Set a new permanent default download folder
  --browser <name>    Use browser cookies (chrome, firefox, edge)
  --force             Re-download even if Reel ID is already in archive.txt
  -h, --help          Show this banner and usage guide

EXAMPLES:
  reelzfetch "https://www.instagram.com/reel/ABC123xyz/" --audio
  reelzfetch "https://www.instagram.com/reel/ABC123xyz/" --both --out "D:\Music\Reels"
  reelzfetch --set-dir "D:\Downloads\Instagram"

EOF
}

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

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "[ERROR] FFmpeg is not installed or not in PATH."
  exit 1
fi

# Interactive mode when launched with no arguments
if [[ $# -eq 0 ]]; then
  print_usage
  read -r -p "Paste Instagram Reel URL (or press Enter to exit): " INPUT_URL
  if [[ -z "${INPUT_URL// }" ]]; then
    exit 0
  fi

  read -r -p "Choose format [1=video, 2=audio, 3=both] (default 1): " FORMAT_CHOICE
  case "$FORMAT_CHOICE" in
    2|audio) MODE="audio" ;;
    3|both)  MODE="both" ;;
    *)       MODE="video" ;;
  esac

  read -r -p "Custom save folder (press Enter to keep current default): " CUSTOM_PATH

  CMD=("$PYTHON_BIN" "$PYTHON_SCRIPT" "$INPUT_URL" "--mode" "$MODE")
  if [[ -n "${CUSTOM_PATH// }" ]]; then
    read -r -p "Save this folder as your permanent default? [y/N]: " MAKE_DEFAULT
    if [[ "$MAKE_DEFAULT" =~ ^[Yy]$ ]]; then
      CMD+=("--set-dir" "$CUSTOM_PATH")
    else
      CMD+=("--out-dir" "$CUSTOM_PATH")
    fi
  fi

  echo ""
  "${CMD[@]}"
  exit $?
fi

URL=""
MODE="video"
BROWSER=""
OUT_DIR=""
SET_DIR=""
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
      [[ -z "$BROWSER" ]] && { echo "[ERROR] --browser requires a browser name."; exit 1; }
      shift 2
      ;;
    --out)
      OUT_DIR="${2:-}"
      [[ -z "$OUT_DIR" ]] && { echo "[ERROR] --out requires a folder path."; exit 1; }
      shift 2
      ;;
    --set-dir)
      SET_DIR="${2:-}"
      [[ -z "$SET_DIR" ]] && { echo "[ERROR] --set-dir requires a folder path."; exit 1; }
      shift 2
      ;;
    --force)
      FORCE_FLAG="--force"
      shift
      ;;
    -*)
      echo "[ERROR] Unknown option: $1"
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

if [[ -z "$URL" && -z "$SET_DIR" ]]; then
  echo "[ERROR] Missing Instagram Reel URL."
  print_usage
  exit 1
fi

print_banner
echo ""

CMD=("$PYTHON_BIN" "$PYTHON_SCRIPT")
[[ -n "$URL" ]] && CMD+=("$URL")
CMD+=("--mode" "$MODE")
[[ -n "$BROWSER" ]] && CMD+=("--browser" "$BROWSER")
[[ -n "$OUT_DIR" ]] && CMD+=("--out-dir" "$OUT_DIR")
[[ -n "$SET_DIR" ]] && CMD+=("--set-dir" "$SET_DIR")
[[ -n "$FORCE_FLAG" ]] && CMD+=("$FORCE_FLAG")

"${CMD[@]}"