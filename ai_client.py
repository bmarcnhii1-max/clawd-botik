import re
import threading

import requests
from PySide6.QtCore import QObject, Signal

from i18n import ui


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
        return bool(self.config.get("ai_enabled") and base and key and model)

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

    def _worker(self, cfg, messages, max_tokens):
        reply = ""
        error = ""
        t = ui(cfg.get("lang", "ru"))
        local = str(cfg.get("ai_mode", "cloud")).lower() == "local"
        try:
            base, key, model, local = self.active_settings(cfg)
            url = base + "/chat/completions"
            headers = {
                "Authorization": "Bearer " + key,
                "X-API-Key": key,
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.9,
            }
            if local:
                payload["reasoning_effort"] = "none"
            timeout = max(5, min(600, int(cfg.get("ai_timeout", 120) or 120)))
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            if response.status_code == 200:
                reply = self._extract(response.json()) or ""
                if not reply:
                    error = t["ai_empty"]
            else:
                error = "HTTP %d: %s" % (response.status_code, str(response.text)[:150])
        except Exception as exc:
            if local and isinstance(exc, requests.exceptions.ConnectionError):
                error = t["ai_local_down"]
            else:
                error = type(exc).__name__ + ": " + str(exc)
        self.finished.emit(reply, error)

    @staticmethod
    def _extract(data):
        choices = data.get("choices") or []
        if not choices:
            return None
        choice = choices[0] or {}
        message = choice.get("message") or {}
        content = message.get("content")
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
            r"<think\b[^>]*>.*?</think\s*>",
            "",
            content,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()
        if "</think" in content.lower():
            tail = re.split(r"</think\s*>", content, flags=re.IGNORECASE)[-1].strip()
            if tail:
                content = tail
        return content or None
