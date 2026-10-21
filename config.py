import copy
import json
import os
import sys

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")

DEFAULTS = {
    "ai_enabled": True,
    "ai_mode": "cloud",
    "ai_base_url": "",
    "ai_key": "",
    "ai_model": "",
    "ai_local_base_url": "http://127.0.0.1:11434/v1",
    "ai_local_key": "ollama",
    "ai_local_model": "gemma4-e2b-local",
    "ai_persona": "",
    "ai_timeout": 120,
    "ai_history": [],
    "size": 1,
    "color": 0,
    "gravity": False,
    "wander": True,
    "phrases": True,
    "lang": "ru",
    "sleep_seconds": 180,
    "always_on_top": True,
    "pos_x": None,
    "pos_y": None,
}


def _load_env():
    values = {}
    path = os.path.join(APP_DIR, ".env")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            for raw in handle:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                if key.startswith("export "):
                    key = key[7:].strip()
                values[key] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    for key, value in os.environ.items():
        if key.startswith("CLAWD_"):
            values[key] = value
    return values


def load_config():
    data = copy.deepcopy(DEFAULTS)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            data.update(loaded)
    except Exception:
        pass
    env = _load_env()
    for config_key, env_key in (
        ("ai_base_url", "CLAWD_AI_BASE_URL"),
        ("ai_key", "CLAWD_AI_KEY"),
        ("ai_model", "CLAWD_AI_MODEL"),
    ):
        if env.get(env_key):
            data[config_key] = env[env_key]
    return data


def save_config(data):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
    except Exception:
        pass
