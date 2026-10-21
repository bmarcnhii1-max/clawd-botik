# Clawd — Desktop AI Pet

A delightful pixel pet for your Windows or Linux desktop. Watch it walk, sleep, and dream. Interact with it through clicks and drags. Chat with it using any OpenAI-compatible AI API or a local Ollama model.

## Features

- Transparent always-on-top pixel pet with smooth animations
- Full interaction support: drag, throw, pet, and tap
- Physics simulation: gravity, autonomous walking, sleeping, and dream bubbles
- Six customizable color palettes and three size options
- Multi-language UI: English, Russian, Ukrainian
- AI-powered chat with conversation history
- Cloud AI mode: works with any OpenAI-compatible API endpoint
- Local AI mode: run privately with Ollama (fast replies, no extended thinking)
- System tray integration with single-instance protection
- Optional Windows executable (no autostart, portable)

## Requirements

- **OS**: Windows 10/11 or Linux (X11 recommended; Wayland works via XWayland)
- **Python**: 3.10 or later (tested up to 3.14)
- **Ollama**: Optional, only needed if you want to use local AI models

## Quick Start (Windows)

```powershell
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run Clawd
python main.py
```

**Alternative:** After installing dependencies, simply run:
```powershell
run.bat
```

## Quick Start (Linux)

X11 is fully tested; Wayland works through XWayland (AppIndicator extension may be needed on GNOME).

### Install dependencies

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip libgl1 libegl1 libxcb-cursor0 \
  libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0
```

### Run Clawd

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x run.sh
./run.sh
```

### Troubleshoot on Wayland

If transparency, window positioning, or the tray icon misbehave:
```bash
QT_QPA_PLATFORM=xcb ./run.sh
```

**Note:** `build.bat` and `setup_local_model.ps1` are Windows-only. On Linux, install Ollama separately using its official installer; `config.py` and `.env` work the same way.

## AI Configuration

Clawd works perfectly fine without AI (it will walk, sleep, and dream). Chat requires either a cloud API or a local Ollama model.

### Option 1: Cloud API (OpenAI-compatible)

**Via UI:**
1. Right-click the pet → **AI settings…**
2. Enter your API URL, API key, and model name
3. Save and start chatting

**Via config file:**
1. Copy `config.example.json` to `config.json`
2. Edit the AI settings
3. Restart Clawd

(`config.json` is git-ignored)

### Option 2: Environment variables

Create or edit `.env`:

```dotenv
CLAWD_AI_BASE_URL=https://api.example.com/v1
CLAWD_AI_MODEL=model-name
CLAWD_AI_KEY=your-api-key
```

Environment variables override `config.json` values. (`.env` is git-ignored)

### Option 3: Local Ollama model

**Automated setup (Windows):**
```powershell
powershell -ExecutionPolicy Bypass -File .\setup_local_model.ps1
```
This downloads Gemma 4 E2B (~3.1 GB) and configures it automatically.

**Manual setup (all platforms):**
```bash
ollama pull gemma4:e2b
```
Then set `ai_local_model` to `gemma4:e2b` in `config.json`, and select **AI model → Local — Gemma 4 E2B** in the tray menu.

## Controls

| Action | Effect |
|--------|--------|
| **Left click** | Tap or pet the pet |
| **Drag** | Move the pet around the screen |
| **Drag + throw** | Flick the pet to make it fly |
| **Drag + shake** | Cycle through languages: English → Russian → Ukrainian |
| **Right click** | Open context menu |
| **Double-click tray icon** | Toggle pet visibility |

**Behavior:** The pet automatically falls asleep after 3 minutes of inactivity and may show dream bubbles while sleeping.

## Building a Windows Executable

### Full build

```powershell
pip install -r requirements-dev.txt
build.bat
```

Output: `dist\Clawd.exe` (standalone executable)

**Note:** Models, `config.json`, `.env`, and build artifacts are *not* bundled—keep them in the same directory as the executable.

### Fast build (for development)

```powershell
build.bat fast
```

This reuses the PyInstaller cache and builds a one-folder app (`dist\Clawd\Clawd.exe`) for quicker iterations.

## Project Structure

| File | Purpose |
|------|---------|
| `main.py` | Entry point, system tray menu, single-instance protection |
| `pet_window.py` | Pet behavior, animations, physics, drag/shake handling |
| `sprite.py` | Pixel sprite frames and color palettes |
| `bubble.py` | Speech bubbles and dream visualizations |
| `dialogs.py` | Chat window and settings UI |
| `ai_client.py` | HTTP client for OpenAI-compatible APIs |
| `config.py` | Configuration management and `.env` loading |
| `i18n.py` | Internationalization (language support) |
| `phrases.py` | Pet dialogue, dreams, and AI system prompts |
| `setup_local_model.ps1` | Helper script for local Ollama model setup (Windows) |
| `run.sh` | Linux launcher script |
| `build.bat` | PyInstaller build automation (Windows) |

## Code Signing

Clawd is applying to the SignPath Foundation for free code signing of Windows release binaries. After approval, GitHub Actions releases will be signed via SignPath.io. See [CODE_SIGNING.md](CODE_SIGNING.md) for details.

## Privacy

**Clawd collects zero telemetry or analytics.** See [PRIVACY.md](PRIVACY.md) for the full privacy policy.

## Security

- **Never commit** `config.json`, `.env`, API keys, downloaded models, or build artifacts
- **Revoke credentials** if they are ever committed or shared (even accidentally)
- `.env.bait` is a decoy file for scanner detection—the app never reads it
- **Network activity** is limited to your configured API endpoint or local Ollama server only
- **No tracking, no telemetry, no analytics**

## Contributing

This is a solo hobby project. Feel free to fork and modify for personal use!

## Test

Минимальная проверка репозитория.

## License

MIT License. See [LICENSE](LICENSE) for details.
