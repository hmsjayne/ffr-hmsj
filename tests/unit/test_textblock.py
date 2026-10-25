import pytest

from doslib.textblock import TextBlock
from stream.inputstream import InputStream


@pytest.mark.parametrize("text", [
    "",
    "Potion",
    "You obtain: Excalibur",
    "Line one\nLine two",
    "A B? C!",
    "«Hello»",
    "é",
])
def test_text_round_trip(text):
    encoded = TextBlock.encode_text(text)
    assert encoded.endswith(b"\x00")

    decoded = TextBlock._as_ascii(InputStream(encoded, check_alignment=False))
    assert decoded == text + "\x00"


def test_text_escape_helpers():
    assert TextBlock._escape(0x41) == "\\x41"
    assert TextBlock._escape(0x8140) == "\\u8140"
    assert TextBlock._escape(0x253264) == "\\U00253264"


def test_encode_text_appends_null_terminator():
    assert TextBlock.encode_text("") == b"\x00"
    assert TextBlock.encode_text("A") == b"\x82\x60\x00"


def test_textblock_setitem_encodes_strings():
    block = TextBlock.__new__(TextBlock)
    block.strings = [None]

    block[0] = "Potion"

    assert block.strings[0] == TextBlock.encode_text("Potion")


def test_unknown_character_is_rejected():
    # TextBlock deliberately supports the game's character table, not arbitrary
    # Unicode. This documents the current behavior until the codec is replaced.
    with pytest.raises(ValueError):
        TextBlock.encode_text("Ω")


def test_tripointer_set_description_writes_description_slot():
    from doslib.tripointertext import TriPointerTextBlock

    block = TriPointerTextBlock.__new__(TriPointerTextBlock)
    block.strings = [None, None, None, None, None, None]

    block.set_description(1, "Description")

    assert block.strings[5] == TextBlock.encode_text("Description")
    assert block.strings[3] is None
