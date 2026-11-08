import json

import pytest

import config as config_mod


def test_coerce_bool_int_choice():
    c = config_mod._coerce({"size": 99, "color": -3, "lang": "xx", "ai_timeout": "abc", "gravity": "yes", "wander": 0})
    assert c["size"] == 3
    assert c["color"] == 0
    assert c["lang"] == "ru"
    assert c["ai_timeout"] == 120
    assert c["gravity"] is True
    assert c["wander"] is False


def test_coerce_history_and_coord():
    c = config_mod._coerce({
        "ai_history": [{"role": "user", "content": "hi"}, {"role": "x", "content": "bad"}, {"role": "assistant", "content": ""}],
        "pos_x": "12.6",
        "pos_y": float("inf"),
    })
    assert c["ai_history"] == [{"role": "user", "content": "hi"}]
    assert c["pos_x"] == 13
    assert c["pos_y"] is None


def test_parse_env_value():
    assert config_mod._parse_env_value('value # comment') == "value"
    assert config_mod._parse_env_value('"quoted # not comment"') == 'quoted # not comment'
    assert config_mod._parse_env_value("'single'") == "single"
    assert config_mod._parse_env_value('""double""') == '"double"'


def test_save_preserves_unknown_and_migrates(tmp_path, monkeypatch):
    target = str(tmp_path / "config.json")
    monkeypatch.setattr(config_mod, "CONFIG_PATH", target)
    monkeypatch.setattr(config_mod, "ERROR_LOG_PATH", str(tmp_path / "clawd-error.log"))
    # simulate file with unknown key
    (tmp_path / "config.json").write_text(json.dumps({"always_on_top": True, "size": 2}), encoding="utf-8")
    loaded = config_mod.load_config()
    assert loaded["size"] == 2
    config_mod.save_config(loaded)
    saved = json.loads((tmp_path / "config.json").read_text(encoding="utf-8"))
    assert saved["always_on_top"] is True


def test_set_config_path(tmp_path):
    old = config_mod.CONFIG_PATH
    try:
        p = config_mod.set_config_path(str(tmp_path / "sub" / "cfg.json"))
        assert p == str(tmp_path / "sub" / "cfg.json")
        assert config_mod.get_config_path() == p
    finally:
        config_mod.set_config_path(old)
