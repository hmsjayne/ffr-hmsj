import random

import pytest

from doslib.data_source import InMemoryDataSource
from randomizer.seed import (
    InvalidSeedError,
    generate_seed,
    normalize_seed,
    seed_bytes,
    seed_checksum,
)


def test_normalize_seed_trims_and_preserves_case_and_spaces():
    assert normalize_seed("  Voyage of the Cactuar  ") == "Voyage of the Cactuar"
    assert normalize_seed("Test") == "Test"
    assert normalize_seed("A" * 32) == "A" * 32


@pytest.mark.parametrize("seed", ["", "   ", "A" * 33, "café", "line\nbreak"])
def test_normalize_seed_rejects_invalid_values(seed):
    with pytest.raises(InvalidSeedError):
        normalize_seed(seed)


def test_seed_bytes_are_stable_and_depend_on_seed():
    assert seed_bytes("test") == seed_bytes("test")
    assert seed_bytes("test") != seed_bytes("Test")
    assert len(seed_bytes("test")) == 32
    assert seed_checksum("test") == seed_bytes("test").hex()[:10]


def test_generate_seed_uses_word_list():
    source = InMemoryDataSource({
        "static/seed_data.toml": (
            'titles = ["The"]\n'
            'prefixes = ["Voyage of"]\n'
            'creatures = ["Cactuar"]\n'
        )
    })

    assert generate_seed(source, random.Random(1)) == "The Voyage of Cactuar"


def test_generate_seed_falls_back_when_word_list_is_missing():
    seed = generate_seed(InMemoryDataSource({}), random.Random(1))

    assert 1 <= len(seed) <= 32
    assert all(0x20 <= ord(char) <= 0x7E for char in seed)
