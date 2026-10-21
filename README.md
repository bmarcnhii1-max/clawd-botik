# Clawd — pixel desktop pet

A tiny pixel pet for Windows. It lives on your desktop, walks around, reacts to clicks and drags, sleeps, dreams, and can chat through an OpenAI-compatible API or a local Ollama model.

## Features

- Transparent always-on-top desktop pet with pixel animations.
- Drag, throw, pet, and tap interactions.
- Gravity, autonomous walking, sleeping, and dream bubbles.
- Six color palettes and three sizes.
- Russian, Ukrainian, and English UI.
- AI chat with persistent short-term history.
- Cloud mode for any OpenAI-compatible endpoint.
- Local mode for Ollama, with thinking disabled for fast replies.
- System tray menu and single-instance behavior.
- Optional Windows executable build (no autostart).

## Requirements

- Windows 10/11 or Linux (X11 recommended; Wayland via XWayland).
- Python 3.10+ (tested with Python 3.14).
- Ollama only if you want the local model.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Or run `run.bat` after installing the dependencies.

## Linux

The Python version runs on Linux. X11 is the best-tested setup; Wayland usually works through XWayland. The tray icon may require an AppIndicator extension on GNOME.

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip libgl1 libegl1 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
chmod +x run.sh
./run.sh
```

If transparency, window positioning, or the tray icon misbehave on Wayland, force X11:

```bash
QT_QPA_PLATFORM=xcb ./run.sh
```

`build.bat` and `setup_local_model.ps1` are Windows-only. On Linux, run from source and install Ollama with its official installer; `config.py` and `.env` work the same way.

## AI setup

Clawd works without AI, but chat needs either a cloud endpoint or a local Ollama model.

### Cloud / OpenAI-compatible API

1. Open the tray menu.
2. Go to **AI settings…**.
3. Enter the API URL, API key, and model name.
4. Save and ask Clawd something.

You can also copy `config.example.json` to `config.json` and edit it. `config.json` is ignored by Git.

### Environment variables

Copy `.env.example` to `.env` and fill in your own values:

```dotenv
CLAWD_AI_BASE_URL=https://api.example.com/v1
CLAWD_AI_MODEL=model-name
CLAWD_AI_KEY=your-key
```

`.env` is ignored by Git. Environment variables override the corresponding values from `config.json`.

### Local Ollama model

1. Install and start Ollama.
2. Run the helper script:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_local_model.ps1
```

It downloads a text-only Gemma 4 E2B Q4_K_M GGUF (about 3.1 GB) into `models/` and creates the Ollama model `gemma4-e2b-local`.

Alternatively, use the official Ollama model:

```powershell
ollama pull gemma4:e2b
```

Then set `ai_local_model` to `gemma4:e2b` in `config.json`.

Finally, choose **AI model → Local — Gemma 4 E2B** in the tray menu.

## Controls

- Left click: tap / pet.
- Drag: move the pet; throw it to make it fly.
- Shake while dragging: cycle Russian → Ukrainian → English.
- Right click: tray-style menu.
- Double click the tray icon: show or hide the pet.

The pet falls asleep after three minutes without interaction and may show dream thoughts while sleeping.

## Build a Windows executable

```powershell
pip install -r requirements-dev.txt
build.bat
```

The result is `dist\Clawd.exe`. Models, `config.json`, `.env`, and generated build artifacts are not bundled into the executable.

For faster local iterations, use `build.bat fast`. It keeps the PyInstaller cache and builds `dist\Clawd\Clawd.exe` as a one-folder app instead of repacking the single-file executable every time.

## Project layout

| File | Purpose |
| --- | --- |
| `main.py` | Application entry point, tray menu, single instance |
| `pet_window.py` | Pet behavior, animation, sleep, drag and shake handling |
| `sprite.py` | Pixel frames and palettes |
| `bubble.py` | Message and dream bubble |
| `dialogs.py` | Chat and settings dialogs |
| `ai_client.py` | OpenAI-compatible HTTP client |
| `config.py` | Configuration, defaults, `.env` loading |
| `i18n.py` | UI translations |
| `phrases.py` | Speech, dreams, and AI personas |
| `setup_local_model.ps1` | Optional local Gemma setup |
| `run.sh` | Linux launcher |
| `build.bat` | PyInstaller build script |

## Code signing policy

Clawd is applying to the SignPath Foundation for free code signing of Windows release binaries. After approval, release executables built by GitHub Actions will be signed through SignPath.io with a certificate issued to SignPath Foundation. See [CODE_SIGNING.md](CODE_SIGNING.md).

## Privacy

Clawd collects no telemetry or analytics. See [PRIVACY.md](PRIVACY.md).

## Security

- Never commit `config.json`, `.env`, API keys, downloaded models, or build outputs.
- If a credential was ever committed or shared, revoke it and create a new one.
- `.env.bait` is a nonfunctional decoy for automated scanners. The app never reads it.
- The app only contacts the API endpoint you configure or the local Ollama server. It has no telemetry.

## Test

Минимальная проверка репозитория.

## License

MIT. See [LICENSE](LICENSE).
