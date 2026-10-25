import hashlib
import json
import os
from pathlib import Path

import pytest

from randomizer.flags import Flags
from randomizer.oracle import run_case, trace_summary

GOLDEN_PATH = Path(__file__).resolve().parents[1] / "golden" / "rom_hashes.json"
GOLDEN = json.loads(GOLDEN_PATH.read_text())

ROM_ENV = "HMSJAYNE_ROM"
ROM_PATH = Path(os.environ[ROM_ENV]) if os.environ.get(ROM_ENV) else None


def test_golden_manifest_shape():
    assert GOLDEN["schema_version"] == 1
    assert GOLDEN["algorithm_version"] == 1
    assert len(GOLDEN["cases"]) >= 10
    assert GOLDEN["base_rom"]["size"] == 16 * 1024 * 1024

    names = [case["name"] for case in GOLDEN["cases"]]
    assert len(names) == len(set(names))


@pytest.mark.skipif(ROM_PATH is None, reason=f"set {ROM_ENV} to run ROM parity tests")
def test_golden_manifest_matches_supplied_rom():
    assert ROM_PATH is not None
    assert ROM_PATH.is_file(), f"{ROM_ENV} does not point to a file: {ROM_PATH}"

    actual_sha256 = hashlib.sha256(ROM_PATH.read_bytes()).hexdigest()
    assert actual_sha256 == GOLDEN["base_rom"]["sha256"], (
        f"Unsupported ROM: expected {GOLDEN['base_rom']['sha256']}, got {actual_sha256}"
    )


@pytest.mark.skipif(ROM_PATH is None, reason=f"set {ROM_ENV} to run ROM parity tests")
@pytest.mark.parametrize("case", GOLDEN["cases"], ids=[case["name"] for case in GOLDEN["cases"]])
def test_golden_case(case):
    assert ROM_PATH is not None

    flags = Flags()
    for key, value in case["flags"].items():
        setattr(flags, key, value)

    manifest, _randomized_rom, _ips_data = run_case(ROM_PATH, case["seed"], flags)
    summary = trace_summary(manifest["trace"])

    assert manifest["flags_encoded"] == case["flags_encoded"]
    assert manifest["rom"]["sha256"] == case["rom_sha256"]
    assert manifest["rom"]["size"] == case["rom_size"]
    assert manifest["ips"]["sha256"] == case["ips_sha256"]
    assert manifest["ips"]["size"] == case["ips_size"]
    assert summary == case["trace"]
