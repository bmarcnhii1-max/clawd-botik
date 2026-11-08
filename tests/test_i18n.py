from i18n import TEXTS, ui
from phrases import PHRASES_RU, PHRASES_UK, PHRASES_EN, get_phrases, get_default_persona


def test_i18n_keys_match():
    base = set(TEXTS["ru"].keys())
    assert set(TEXTS["uk"].keys()) == base
    assert set(TEXTS["en"].keys()) == base


def test_phrases_keys_match():
    assert set(PHRASES_RU.keys()) == set(PHRASES_UK.keys()) == set(PHRASES_EN.keys())
    assert get_phrases("xx") is PHRASES_RU
    assert get_default_persona("ru")


def test_ui_fallback():
    assert ui("xx") is TEXTS["ru"]
