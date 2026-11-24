# ReelzFetch

**ReelzFetch** is a lightweight, terminal-based CLI utility for downloading Instagram Reels and posts as MP4 videos or extracting their audio into uncompressed 16-bit WAV files.

Built with **Bash**, **Python**, **yt-dlp**, and **FFmpeg**, it runs straight from your terminal with interactive prompts, clickable output links, and automatic duplicate tracking—no bulky GUI or web server required.

---

## Key Features

* **Flexible Output Formats:** Download Reels as video (`--video`), extract clean 16-bit PCM stereo WAV audio (`--audio`), or save both (`--both`).
* **Interactive & Flag Modes:** Run `reelzfetch` with no arguments for step-by-step interactive prompts, or pass flags directly for fast one-line commands.
* **Custom & Persistent Save Folders:** Save files to a one-off folder with `--out` or set a permanent default directory with `--set-dir`.
* **Clickable Terminal Paths:** Outputs `OSC 8` `file:///` links so you can `Ctrl + Click` saved files and folders directly in Windows Terminal, VS Code, or Git Bash.
* **Duplicate Prevention & Logging:** Tracks previously downloaded Reel IDs in `logs/archive.txt` (override anytime with `--force`) and writes timestamped logs to `logs/download.log`.
* **Cross-Platform Terminal Support:** Works on Windows (CMD, PowerShell, Git Bash), macOS, and Linux.

---

## Project Structure

```text
reel-downloader/
├── reelzfetch.sh          # Main Bash CLI entrypoint & interactive menu
├── reelzfetch.bat         # Windows CMD / PowerShell wrapper
├── downloader.py          # Python media engine (yt-dlp + FFmpeg)
├── requirements.txt       # Python package dependencies
├── INSTALL_AND_USAGE.md   # Detailed setup and command guide
├── downloads/             # Default output directory (auto-created)
│   ├── videos/            # Saved .mp4 files
│   └── audio/             # Extracted .wav files
└── logs/                  # Execution logs & download archive (auto-created)
    ├── download.log
    └── archive.txt
```

---

## Tech Stack

| Tool | Role |
| :--- | :--- |
| **Bash** | CLI argument parsing, ASCII banner, and interactive prompts |
| **Python 3** | URL validation, progress rendering, file management, and error handling |
| **yt-dlp** | Instagram media extraction and MP4 downloading |
| **FFmpeg** | Audio extraction and conversion to 44.1 kHz 16-bit stereo WAV |

---

## Quick Start

1. Follow the setup steps in **[INSTALL_AND_USAGE.md](INSTALL_AND_USAGE.md)** to install `Python`, `FFmpeg`, and `yt-dlp`.
2. Run the tool interactively from your terminal:
   ```bash
   reelzfetch
   ```
3. Or pass a URL and format flag directly:
   ```bash
   reelzfetch "https://www.instagram.com/reel/YOUR_REEL_ID/" --audio
   ```

---

## Disclaimer

This tool is intended for personal and educational use. Only download content that you own or have explicit permission from the creator to save, and always respect Instagram's Terms of Service and applicable copyright laws.