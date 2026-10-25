import pytest

from randomizer.ipsfile import IPS_EOF, IPS_MAGIC, apply_patches, load_ips_file, load_ips_files


def _ips_bytes(offset: int, data: bytes) -> bytes:
    return (
        IPS_MAGIC
        + offset.to_bytes(3, "big")
        + len(data).to_bytes(2, "big")
        + data
        + IPS_EOF.to_bytes(3, "big")
    )


def test_load_ips_file(tmp_path):
    path = tmp_path / "simple.ips"
    path.write_bytes(_ips_bytes(0x10, b"\xaa\xbb\xcc"))

    assert load_ips_file(path) == {0x10: (0xAA, 0xBB, 0xCC)}


def test_load_ips_file_rle(tmp_path):
    contents = (
        IPS_MAGIC
        + (0x20).to_bytes(3, "big")
        + (0).to_bytes(2, "big")
        + (4).to_bytes(2, "big")
        + b"\x99"
        + IPS_EOF.to_bytes(3, "big")
    )
    path = tmp_path / "rle.ips"
    path.write_bytes(contents)

    assert load_ips_file(path) == {0x20: (0x99, 0x99, 0x99, 0x99)}


def test_load_ips_files_rejects_duplicate_offsets(tmp_path):
    first = tmp_path / "first.ips"
    second = tmp_path / "second.ips"
    first.write_bytes(_ips_bytes(0x10, b"\x01"))
    second.write_bytes(_ips_bytes(0x10, b"\x02"))

    with pytest.raises(RuntimeWarning, match="Multiple patches"):
        load_ips_files(first, second)


def test_load_ips_files_rejects_bad_header(tmp_path):
    path = tmp_path / "bad.ips"
    path.write_bytes(b"NOTIPS")

    with pytest.raises(RuntimeError, match="invalid header"):
        load_ips_file(path)


def test_apply_patches():
    original = tuple(range(16))
    patched = apply_patches(original, {4: (0xAA, 0xBB), 10: (0xCC,)})
    assert patched == tuple(range(4)) + (0xAA, 0xBB) + tuple(range(6, 10)) + (0xCC,) + tuple(range(11, 16))
