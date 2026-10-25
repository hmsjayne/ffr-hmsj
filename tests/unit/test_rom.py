import struct

import pytest

from doslib.rom import FreeBlock, Rom


def test_pointer_conversions():
    assert Rom.pointer_to_offset(0x8000010) == 0x10
    assert Rom.offset_to_pointer(0x10) == 0x8000010

    with pytest.raises(RuntimeError):
        Rom.pointer_to_offset(0x10)


def test_open_bytestream_and_bounds():
    rom = Rom(bytearray(b"\x00\x01\x02\x03\x04"))

    stream = rom.open_bytestream(1, 3)
    assert stream.get_u8() == 1
    assert stream.get_u8() == 2
    assert stream.get_u8() == 3
    assert stream.is_eos()

    with pytest.raises(RuntimeError):
        rom.open_bytestream(99)


def test_get_lut():
    rom = Rom(bytearray(struct.pack("<II", 0x8000010, 0x8000020)))

    assert rom.get_lut(0, 2) == (0x8000010, 0x8000020)

    with pytest.raises(RuntimeError):
        rom.get_lut(1, 1)


def test_get_string_and_stream():
    rom = Rom(bytearray(b"hello\x00worldEND\x00"))

    assert rom.get_string(0) == bytearray(b"hello\x00")
    stream = rom.get_stream(6, bytearray(b"END"))
    assert bytes(stream._stream) == b"worldEND"


def test_apply_patches():
    rom = Rom(bytearray(b"abcdefghij"))

    patched = rom.apply_patches({
        2: b"XY",
        7: b"ZZZ",
    })

    assert patched.rom_data == bytearray(b"abXYefgZZZ")


def test_apply_patches_rejects_overlap_and_bad_offsets():
    rom = Rom(bytearray(b"abcdefghij"))

    with pytest.raises(RuntimeError, match="already at"):
        rom.apply_patches({2: b"XY", 3: b"Z"})

    with pytest.raises(RuntimeError, match="Invalid patch offset"):
        rom.apply_patches({11: b"Z"})

    with pytest.raises(RuntimeError, match="Is it a pointer"):
        rom.apply_patches({0x8000010: b"Z"})


def test_apply_patches_rejects_patch_past_end():
    rom = Rom(bytearray(b"abcdefghij"))

    with pytest.raises(RuntimeError, match="extends past the end"):
        rom.apply_patches({8: b"XYZ"})


def test_get_event_size():
    rom = Rom(bytearray(b"\x01\x04\xff\xff\x00\x04\xff\xff"))

    assert rom.get_event_size(0) == 8
    assert rom.get_event_size(4) == 4


def test_free_block_allocates_and_fails_cleanly():
    free = FreeBlock(0x1000, 8)

    assert free.allocate("first", 3) == 0x1000
    assert free.allocate("second", 5) == 0x1003

    with pytest.raises(RuntimeError, match="No free space"):
        free.allocate("third", 1)
