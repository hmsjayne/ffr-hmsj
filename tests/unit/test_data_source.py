from pathlib import Path

from doslib.data_source import FileSystemDataSource, InMemoryDataSource
from doslib.dos_utils import load_tsv


def test_filesystem_data_source_reads_files(tmp_path):
    root = tmp_path
    (root / "data").mkdir()
    (root / "data" / "sample.txt").write_text("hello")
    (root / "data" / "sample.bin").write_bytes(b"\x01\x02")
    (root / "data" / "ignored.txt.bak").write_text("nope")

    source = FileSystemDataSource(root)

    assert source.read_text("data/sample.txt") == "hello"
    assert source.read_bytes("data/sample.bin") == b"\x01\x02"
    assert source.list_files("data") == ["ignored.txt.bak", "sample.bin", "sample.txt"]
    assert source.list_files("data", ".txt") == ["sample.txt"]


def test_in_memory_data_source():
    source = InMemoryDataSource({
        "data/text.txt": "hello",
        "data/bytes.bin": b"\x01\x02",
        "data/nested/ignored.txt": "nested",
        "scripts/a.script": "script a",
        "scripts/b.script": "script b",
    })

    assert source.read_text("data/text.txt") == "hello"
    assert source.read_bytes("data/bytes.bin") == b"\x01\x02"
    assert source.list_files("data", ".txt") == ["text.txt"]
    assert source.list_files("scripts", ".script") == ["a.script", "b.script"]


def test_load_tsv_with_in_memory_source():
    source = InMemoryDataSource({
        "data/table.tsv": "name\tvalue\nalpha\t0x10\n",
    })

    assert load_tsv("data/table.tsv", source) == [["alpha", 0x10]]
