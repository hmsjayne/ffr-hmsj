import pytest

from randomizer.patchset import PatchConflictError, PatchSet


def test_patchset_add_and_mapping_operations():
    patches = PatchSet()
    patches.add(4, b"\x01\x02", source="test")
    patches[8] = bytearray(b"\x03")

    assert len(patches) == 2
    assert patches[4] == b"\x01\x02"
    assert patches[8] == b"\x03"
    assert list(patches) == [4, 8]
    assert patches.to_dict() == {4: b"\x01\x02", 8: b"\x03"}


def test_patchset_update_and_conflict():
    patches = PatchSet()
    patches.update({4: b"\x01", 8: b"\x02"}, source="first")

    patches.update({12: b"\x03"})

    assert patches.to_dict() == {4: b"\x01", 8: b"\x02", 12: b"\x03"}

    with pytest.raises(PatchConflictError, match="Multiple patches"):
        patches.update({4: b"\xff"}, source="second")


def test_patchset_delete():
    patches = PatchSet({4: b"\x01"})
    del patches[4]

    assert len(patches) == 0
