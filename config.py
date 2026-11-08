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


def _user_config_dir():
    appdata = os.environ.get("APPDATA")
    if sys.platform.startswith("win") and appdata:
        return os.path.join(appdata, "Clawd")
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return os.path.join(xdg, "clawd")
    try:
        home = os.path.expanduser("~")
    except Exception:
        home = APP_DIR
    if home and os.path.isabs(home):
        return os.path.join(home, ".config", "clawd")
    return APP_DIR


def _cli_config_path():
    argv = sys.argv[1:]
    for i, arg in enumerate(argv):
        if arg == "--config" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--config="):
            return arg[len("--config=") :]
    return ""


def _resolve_config_path():
    explicit = _cli_config_path() or os.environ.get("CLAWD_CONFIG", "").strip() or os.environ.get("CLAWD_CONFIG_FILE", "").strip()
    if explicit:
        if os.path.isabs(explicit):
            return explicit
        return os.path.join(APP_DIR, explicit)
    # Backward compat: existing portable config next to exe wins; otherwise user dir.
    legacy = os.path.join(APP_DIR, "config.json")
    if os.path.exists(legacy):
        return legacy
    return os.path.join(_user_config_dir(), "config.json")


def _resolve_error_log_path(config_path):
    base = os.path.dirname(os.path.abspath(config_path)) or APP_DIR
    return os.path.join(base, "clawd-error.log")


CONFIG_PATH = _resolve_config_path()
ERROR_LOG_PATH = _resolve_error_log_path(CONFIG_PATH)


def get_config_path():
    return CONFIG_PATH


def get_error_log_path():
    return ERROR_LOG_PATH


def set_config_path(path):
    """Override config path (tests / --config)."""
    global CONFIG_PATH, ERROR_LOG_PATH
    CONFIG_PATH = os.path.abspath(path)
    ERROR_LOG_PATH = _resolve_error_log_path(CONFIG_PATH)
    return CONFIG_PATH

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
    "ai_thoughts": True,
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

MAX_SIZE_INDEX = 3
MAX_COLOR_INDEX = 6
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
        "ai_thoughts": _as_bool(data.get("ai_thoughts"), DEFAULTS["ai_thoughts"]),
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


def _parse_env_value(raw_value):
    value = raw_value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    hash_pos = value.find(" #")
    if hash_pos != -1:
        value = value[:hash_pos].strip()
    return value


def _load_env():
    values = {}
    candidates = []
    for cand_dir in (os.path.dirname(CONFIG_PATH), _user_config_dir(), APP_DIR):
        pth = os.path.join(cand_dir, ".env")
        if pth not in candidates:
            candidates.append(pth)
    for path in candidates:
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
                    values[key] = _parse_env_value(value)
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


def _write_atomic(payload, target_path=None):
    target = target_path or CONFIG_PATH
    directory = os.path.dirname(target) or "."
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        pass
    fd, tmp_path = tempfile.mkstemp(prefix=".config-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, target)
        try:
            os.chmod(target, 0o600)
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
        coerced = _coerce(payload)
        # Preserve unknown keys (e.g. always_on_top) that _coerce drops.
        unknown = {}
        if isinstance(data, Config):
            for key, value in data.file_values.items():
                if key not in DEFAULTS:
                    unknown[key] = value
        for key, value in payload.items():
            if key not in DEFAULTS:
                unknown[key] = value
        coerced.update(unknown)
        try:
            _write_atomic(coerced)
        except PermissionError:
            fallback_dir = _user_config_dir()
            if os.path.abspath(fallback_dir) != os.path.abspath(os.path.dirname(CONFIG_PATH) or "."):
                fallback_path = os.path.join(fallback_dir, "config.json")
                _write_atomic(coerced, fallback_path)
                set_config_path(fallback_path)
            else:
                raise
    except Exception as exc:
        _log_save_error(exc)
