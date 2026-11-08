import re
import threading
from urllib.parse import urlsplit

import requests
from PySide6.QtCore import QObject, Signal

from i18n import ui

_LOOPBACK_HOSTS = {"localhost", "127.0.0.1", "::1"}


def _is_loopback(base_url):
    try:
        host = (urlsplit(str(base_url)).hostname or "").lower()
    except ValueError:
        return False
    return host in _LOOPBACK_HOSTS or host.startswith("127.")


class AIClient(QObject):
    finished = Signal(str, str)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config

    @staticmethod
    def active_settings(cfg):
        if str(cfg.get("ai_mode", "cloud")).lower() == "local":
            return (
                str(cfg.get("ai_local_base_url", "")).strip().rstrip("/"),
                str(cfg.get("ai_local_key", "")).strip(),
                str(cfg.get("ai_local_model", "")).strip(),
                True,
            )
        return (
            str(cfg.get("ai_base_url", "")).strip().rstrip("/"),
            str(cfg.get("ai_key", "")).strip(),
            str(cfg.get("ai_model", "")).strip(),
            False,
        )

    def ready(self):
        base, key, model, _ = self.active_settings(self.config)
        return bool(self.config.get("ai_enabled") and base and model and (key or _is_loopback(base)))

    def ask(self, messages, max_tokens=220):
        if not self.ready():
            self.finished.emit("", ui(self.config.get("lang", "ru"))["ai_not_configured"])
            return
        snapshot = dict(self.config)
        threading.Thread(
            target=self._worker,
            args=(snapshot, messages, int(max_tokens)),
            daemon=True,
        ).start()

    @staticmethod
    def _cloud_settings(cfg):
        base = str(cfg.get("ai_base_url", "")).strip().rstrip("/")
        key = str(cfg.get("ai_key", "")).strip()
        model = str(cfg.get("ai_model", "")).strip()
        if base and key and model:
            return base, key, model
        return None

    def _worker(self, cfg, messages, max_tokens):
        t = ui(cfg.get("lang", "ru"))
        local = str(cfg.get("ai_mode", "cloud")).lower() == "local"
        base, key, model, _ = self.active_settings(cfg)
        reply, error, conn_failed = self._attempt(base, key, model, local, messages, max_tokens, cfg, t)
        if local and conn_failed and not reply:
            cloud = self._cloud_settings(cfg)
            if cloud is not None:
                reply, error, _ = self._attempt(cloud[0], cloud[1], cloud[2], False, messages, max_tokens, cfg, t)
        self.finished.emit(reply, error)

    def _attempt(self, base, key, model, local, messages, max_tokens, cfg, t):
        reply = ""
        error = ""
        conn_failed = False
        try:
            url = base + "/chat/completions"
            headers = {"Content-Type": "application/json"}
            if key:
                headers["Authorization"] = "Bearer " + key
                headers["X-API-Key"] = key
            try:
                temp = float(cfg.get("ai_temperature", 0.9) or 0.9)
            except (TypeError, ValueError, OverflowError):
                temp = 0.9
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": max(0.0, min(2.0, temp)),
            }
            if local:
                payload["reasoning_effort"] = "none"
            try:
                raw_timeout = cfg.get("ai_timeout", 120)
                timeout = max(5, min(600, int(float(raw_timeout or 120))))
            except (TypeError, ValueError, OverflowError):
                timeout = 120
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                reply = self._extract(response.json()) or ""
                if not reply:
                    error = t["ai_empty"]
            elif response.status_code in (401, 403):
                error = "HTTP %d: invalid key" % response.status_code
            elif response.status_code == 404:
                error = "HTTP %d: model not found" % response.status_code
            elif response.status_code == 429:
                error = "HTTP %d: rate limited" % response.status_code
            else:
                error = "HTTP %d" % response.status_code
        except Exception as exc:
            if isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
                conn_failed = True
                if local:
                    error = t["ai_local_down"].format(base=base or "?")
                else:
                    error = type(exc).__name__ + ": " + str(exc)
            else:
                error = type(exc).__name__ + ": " + str(exc)
        return reply, error, conn_failed

    @staticmethod
    def _extract(data):
        if not isinstance(data, dict):
            return None
        choices = data.get("choices") or []
        if not choices:
            return None
        if not isinstance(data, dict):
            return None
        choice = choices[0] or {}
        if not isinstance(choice, dict):
            return None
        message = choice.get("message") or {}
        if not isinstance(message, dict):
            message = {}
        content = message.get("content")
        if isinstance(content, dict):
            content = content.get("text") or content.get("content") or ""
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict):
                    if part.get("text"):
                        parts.append(str(part["text"]))
                elif isinstance(part, str):
                    parts.append(part)
            content = "".join(parts)
        if not content:
            content = message.get("reasoning_content") or choice.get("text")
        if content is None:
            return None
        content = str(content).strip()
        content = re.sub(
            r"<(think|thinking|reasoning)\b[^>]*>.*?</(?:think|thinking|reasoning)\s*>",
            "",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()
        closing = re.search(r"</(?:think|thinking|reasoning)\s*>", content, flags=re.IGNORECASE)
        if closing:
            content = content[closing.end():].strip()
        else:
            content = re.sub(
                r"</?(?:think|thinking|reasoning)\b[^>]*>",
                "",
                content,
                flags=re.IGNORECASE,
            ).strip()
        return content or None
