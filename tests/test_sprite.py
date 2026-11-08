from PySide6.QtWidgets import QApplication

import sprite

app = QApplication.instance() or QApplication([])


def test_all_palettes_render():
    for idx in range(len(sprite.PALETTES)):
        _, body, eye = sprite.palette(idx)
        key = ("open", 0, "normal", "stand", 0, False, None)
        pix = sprite.render_frame(key, 6, body, eye, sprite.body_shape(idx))
        assert not pix.isNull()
        assert pix.width() == 18 * 6


def test_omnom_expressions():
    _, body, eye = sprite.palette(sprite.OMNOM_INDEX)
    for eyes in ("open", "blink", "happy", "sleep", "dizzy", "surprised", "angry"):
        pix = sprite.render_frame((eyes, 0, "normal", "stand", 0, False, None), 6, body, eye, "omnom")
        assert not pix.isNull()


def test_sprite_size():
    assert sprite.sprite_size(6) == (108, 78)
