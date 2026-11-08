# Contributing

Solo hobby project. PRs welcome for personal use forks.

```powershell
pip install -r requirements-dev.txt
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests -q
python -m py_compile ai_client.py bubble.py config.py dialogs.py i18n.py main.py make_icon.py pet_window.py phrases.py sprite.py
```

- Never commit `config.json`, `.env`, keys, models, dist/
- Add tests for new config/ai/sprite behavior
- Keep ru/uk/en translations in sync (tests/test_i18n.py enforces)
