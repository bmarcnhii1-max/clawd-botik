import copy
import json
import math
import os
import sys
import tempfile

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
ERROR_LOG_PATH = os.path.join(APP_DIR, "clawd-error.log")

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
    "ai_max_tokens": 220,
    "ai_history": [],
    "size": 1,
    "color": 0,
    "gravity": False,
    "wander": True,
    "phrases": True,
    "lang": "ru",
    "sleep_seconds": 180,
    "pos_x": None,
    "pos_y": None,
}

ENV_KEYS = {
    "ai_base_url": "CLAWD_AI_BASE_URL",
    "ai_key": "CLAWD_AI_KEY",
    "ai_model": "CLAWD_AI_MODEL",
}

MAX_SIZE_INDEX = 2
MAX_COLOR_INDEX = 5
LANGUAGES = ("ru", "uk", "en")
AI_MODES = ("cloud", "local")


class Config(dict):
    """Runtime config that remembers which values came from the environment."""

    def __init__(self, values=None, env_overrides=None, file_values=None):
        super().__init__(values or {})
        self.env_overrides = set(env_overrides or ())
        self.file_values = dict(file_values or {})

    def set_user_value(self, key, value):
        self[key] = value
        self.env_overrides.discard(key)
        self.file_values.pop(key, None)


def _as_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("1", "true", "yes", "on"):
            return True
        if text in ("0", "false", "no", "off", ""):
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _as_int(value, default, low, high):
    try:
        if isinstance(value, bool):
            raise ValueError
        number = int(float(value))
    except (TypeError, ValueError, OverflowError):
        return default
    if number < low:
        return low
    if number > high:
        return high
    return number


def _as_str(value, default="", limit=2000):
    if value is None:
        return default
    if not isinstance(value, str):
        value = str(value)
    return value.strip()[:limit]


def _as_choice(value, choices, default):
    value = _as_str(value, default)
    return value if value in choices else default


def _as_coord(value):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number):
        return None
    return int(round(number))


def _as_history(value):
    if not isinstance(value, list):
        return []
    history = []
    for item in value[-12:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            history.append({"role": role, "content": content[:1000]})
    return history


def _coerce(raw):
    data = copy.deepcopy(DEFAULTS)
    if isinstance(raw, dict):
        data.update(raw)
    return {
        "ai_enabled": _as_bool(data.get("ai_enabled"), DEFAULTS["ai_enabled"]),
        "ai_mode": _as_choice(data.get("ai_mode"), AI_MODES, DEFAULTS["ai_mode"]),
        "ai_base_url": _as_str(data.get("ai_base_url"), "", 500),
        "ai_key": _as_str(data.get("ai_key"), "", 500),
        "ai_model": _as_str(data.get("ai_model"), "", 200),
        "ai_local_base_url": _as_str(data.get("ai_local_base_url"), DEFAULTS["ai_local_base_url"], 500),
        "ai_local_key": _as_str(data.get("ai_local_key"), DEFAULTS["ai_local_key"], 500),
        "ai_local_model": _as_str(data.get("ai_local_model"), DEFAULTS["ai_local_model"], 200),
        "ai_persona": _as_str(data.get("ai_persona"), "", 4000),
        "ai_timeout": _as_int(data.get("ai_timeout"), DEFAULTS["ai_timeout"], 10, 600),
        "ai_max_tokens": _as_int(data.get("ai_max_tokens"), DEFAULTS["ai_max_tokens"], 16, 4096),
        "ai_history": _as_history(data.get("ai_history")),
        "size": _as_int(data.get("size"), DEFAULTS["size"], 0, MAX_SIZE_INDEX),
        "color": _as_int(data.get("color"), DEFAULTS["color"], 0, MAX_COLOR_INDEX),
        "gravity": _as_bool(data.get("gravity"), DEFAULTS["gravity"]),
        "wander": _as_bool(data.get("wander"), DEFAULTS["wander"]),
        "phrases": _as_bool(data.get("phrases"), DEFAULTS["phrases"]),
        "lang": _as_choice(data.get("lang"), LANGUAGES, DEFAULTS["lang"]),
        "sleep_seconds": _as_int(data.get("sleep_seconds"), DEFAULTS["sleep_seconds"], 0, 86400),
        "pos_x": _as_coord(data.get("pos_x")),
        "pos_y": _as_coord(data.get("pos_y")),
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
    file_values = {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            file_values = loaded
    except Exception:
        pass

    data = dict(DEFAULTS)
    data.update({key: value for key, value in file_values.items() if key in DEFAULTS})

    env_overrides = set()
    env = _load_env()
    for config_key, env_key in ENV_KEYS.items():
        value = _as_str(env.get(env_key), "", 500)
        if value:
            data[config_key] = value
            env_overrides.add(config_key)

    return Config(_coerce(data), env_overrides, file_values)


def _log_save_error(exc):
    try:
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as handle:
            handle.write("config save failed: %s: %s\n" % (type(exc).__name__, exc))
    except Exception:
        pass


def _write_atomic(payload):
    directory = os.path.dirname(CONFIG_PATH) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".config-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, CONFIG_PATH)
        try:
            os.chmod(CONFIG_PATH, 0o600)
        except OSError:
            pass
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def save_config(data):
    try:
        payload = dict(data)
        if isinstance(data, Config):
            for key in data.env_overrides:
                file_value = data.file_values.get(key)
                if file_value is None:
                    payload.pop(key, None)
                elif str(file_value).strip() == str(data.get(key, "")).strip():
                    payload.pop(key, None)
                else:
                    payload[key] = file_value
        _write_atomic(_coerce(payload))
    except Exception as exc:
        _log_save_error(exc)
