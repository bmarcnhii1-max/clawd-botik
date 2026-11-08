import config as config_mod
import sprite
from phrases import get_persona_preset, list_persona_presets


def test_coerce_new_fields():
    c = config_mod._coerce({"ai_temperature": 5, "ai_thought_interval": 3, "opacity": 2, "accessory": "bow", "affection": 150})
    assert c["ai_temperature"] == 2.0
    assert c["ai_thought_interval"] == 5
    assert c["opacity"] == 1.0
    assert c["accessory"] == "bow"
    assert c["affection"] == 100


def test_new_palettes():
    assert len(sprite.PALETTES) == 9
    assert sprite.palette(7)[0] == "Зимний"
    assert sprite.palette(8)[0] == "Лунный"
    assert sprite.OMNOM_INDEX == 6


def test_accessory():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    _, body, eye = sprite.palette(0)
    pix = sprite.render_frame(("open", 0, "normal", "stand", 0, False, None), 6, body, eye, "claw")
    hat = sprite.apply_accessory(pix, "hat", 6)
    bow = sprite.apply_accessory(pix, "bow", 6)
    none = sprite.apply_accessory(pix, "none", 6)
    assert not hat.isNull() and not bow.isNull() and not none.isNull()


def test_skins_discovery(tmp_path):
    base = tmp_path / "skins"
    base.mkdir()
    (base / "a").mkdir()
    (base / "a" / "frame.png").write_bytes(b"x")
    (base / "b").mkdir()
    (base / "b" / "plain").write_text("no")
    assert sprite.list_custom_skins(str(base)) == ["a"]


def test_persona_presets():
    assert list_persona_presets("ru")
    assert get_persona_preset("friendly", "ru")
    assert get_persona_preset("joker", "en")
