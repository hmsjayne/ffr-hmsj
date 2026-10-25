from pathlib import Path

import pytest

from doslib.dos_utils import decode_permission_string, load_tsv, resolve_path


def test_decode_permission_string_known_bits():
    assert decode_permission_string("") == 0
    assert decode_permission_string("f") == 0x0001
    assert decode_permission_string("K") == 0x0100
    assert decode_permission_string("fK") == 0x0101
    assert decode_permission_string("t") == 0x0002
    assert decode_permission_string("N") == 0x0200


def test_decode_permission_string_rejects_unknown_character():
    with pytest.raises(KeyError):
        decode_permission_string("?")


def test_load_tsv_parses_types(tmp_path):
    path = tmp_path / "sample.tsv"
    path.write_text(
        "name\tcount\tenabled\tmissing\tvalue\n"
        "alpha\t0x10\tTRUE\t\tplain text\n"
        "beta\t-2\tfalse\tNone\t123\n"
    )

    assert load_tsv(str(path)) == [
        ["alpha", 0x10, True, None, "plain text"],
        ["beta", -2, False, None, 123],
    ]


def test_load_tsv_pads_short_rows(tmp_path):
    path = tmp_path / "short.tsv"
    path.write_text("a\tb\tc\n1\n")

    assert load_tsv(str(path)) == [[1, None, None]]


def test_resolve_path_without_pyinstaller_returns_absolute_path():
    resolved = resolve_path("data/ItemData.tsv")

    assert Path(resolved).is_absolute()
    assert Path(resolved).name == "ItemData.tsv"
    assert Path(resolved).is_file()
    assert resolve_path(Path("data/ItemData.tsv")) == resolved
