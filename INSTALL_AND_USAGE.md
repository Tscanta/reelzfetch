# Installation & Usage Guide

This guide covers everything needed to install **ReelzFetch** on your machine and run it from any terminal.

---

## 1. Prerequisites

Make sure the following system tools are installed and available in your system `PATH`:

1. **Python 3.10+**
   * **Windows:** Install from [python.org](https://www.python.org/) (check **"Add Python to PATH"** during installation).
   * **macOS:** `brew install python`
   * **Linux (Ubuntu/Debian):** `sudo apt update && sudo apt install -y python3 python3-pip`

2. **FFmpeg** *(required for converting audio to WAV)*
   * **Windows:** `winget install Gyan.FFmpeg` (restart your terminal afterward)
   * **macOS:** `brew install ffmpeg`
   * **Linux (Ubuntu/Debian):** `sudo apt update && sudo apt install -y ffmpeg`

3. **Bash Environment**
   * **Windows:** Install [Git for Windows](https://gitforwindows.org/) (includes Git Bash, which `reelzfetch.bat` uses behind the scenes).
   * **macOS / Linux:** Bash is pre-installed.

---

## 2. Installation

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/reel-downloader.git
   cd reel-downloader
   ```

2. **Install the Python dependency (`yt-dlp`):**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify your tools are detected:**
   ```bash
   python --version
   python -c "import yt_dlp.version; print(yt_dlp.version.__version__)"
   ffmpeg -version
   ```

---

## 3. Run `reelzfetch` Globally from Any Folder

### Windows (CMD & PowerShell)
1. Ensure `reelzfetch.bat` and `reelzfetch.sh` are in the project root folder.
2. Add the project folder path (e.g., `D:\C 4 Coding\reel-downloader`) to your **User `PATH`** environment variable:
   * Press `Win + S`, open **"Edit environment variables for your account"**, edit **Path**, click **New**, and paste your folder path.
   * Or run this in PowerShell (replace the path with your own):
     ```powershell
     [Environment]::SetEnvironmentVariable("Path", $env:Path + ";D:\C 4 Coding\reel-downloader", "User")
     ```
3. **Close and reopen** CMD or PowerShell. You can now type `reelzfetch` from any directory.

### macOS / Linux / Git Bash
1. Make the script executable:
   ```bash
   chmod +x reelzfetch.sh
   ```
2. Add an alias to your `~/.bashrc` or `~/.zshrc`:
   ```bash
   echo 'alias reelzfetch="/full/path/to/reel-downloader/reelzfetch.sh"' >> ~/.bashrc
   source ~/.bashrc
   ```

---

## 4. How to Use ReelzFetch

### Interactive Mode
Run `reelzfetch` with no arguments to view the banner, see your current default save folder, and follow the interactive prompts:
```bash
reelzfetch
```

### Command-Line Usage
```bash
reelzfetch "<INSTAGRAM_REEL_URL>" [MODE] [OPTIONS]
```

#### Modes
| Flag | Description |
| :--- | :--- |
| `--video` | Download the Reel as an `.mp4` video *(default)* |
| `--audio` | Extract the audio track and save as a 16-bit `.wav` file |
| `--both` | Save both the `.mp4` video and `.wav` audio |

#### Options
| Flag | Description |
| :--- | :--- |
| `--out <dir>` | Save files to a custom folder for this download only |
| `--set-dir <dir>` | Set a new permanent default download folder (saved in `config.json`) |
| `--browser <name>` | Use cookies from a supported browser (`chrome`, `firefox`, `edge`) for restricted posts |
| `--force` | Re-download a Reel even if its ID is already logged in `logs/archive.txt` |
| `-h`, `--help` | Display the ASCII banner and usage guide |

---

## 5. Examples

```bash
# Download a Reel as MP4 video
reelzfetch "https://www.instagram.com/reel/ABC123xyz/" --video

# Extract WAV audio only
reelzfetch "https://www.instagram.com/reel/ABC123xyz/" --audio

# Save both MP4 and WAV to a one-time custom folder
reelzfetch "https://www.instagram.com/reel/ABC123xyz/" --both --out "D:\Music\Samples"

# Change your permanent default download folder
reelzfetch --set-dir "D:\Downloads\Instagram"

# Re-download a previously downloaded Reel
reelzfetch "https://www.instagram.com/reel/ABC123xyz/" --audio --force
```

---

## 6. Troubleshooting

* **Instagram returns no media info / login wall:**
  Instagram frequently changes its web endpoints or restricts anonymous access. First update `yt-dlp`:
  ```bash
  pip install -U yt-dlp
  ```
  If a post still requires authentication, pass `--browser chrome` (or `firefox` / `edge`) while logged into Instagram in that browser.
* **`reelzfetch` is not recognized in CMD/PowerShell:**
  Make sure you restarted your terminal after adding the folder to your User `PATH`, and confirm both `reelzfetch.bat` and `reelzfetch.sh` exist in that folder.
* **Checking detailed errors:**
  Every run writes detailed status and FFmpeg diagnostic messages to `logs/download.log`.