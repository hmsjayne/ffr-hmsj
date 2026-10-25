import argparse
import hashlib
import json

from randomizer.api import RandomizerResult
from randomizer.flags import Flags
from randomizer.oracle import asset_manifest, build_flags, canonical_json_sha256, trace_summary


def test_build_flags_maps_cli_options():
    args = argparse.Namespace(
        no_shuffle=True,
        standard_shops=False,
        standard_treasure=True,
        default_start_gear=False,
        default_bosses=True,
        new_items=True,
        fiend_ribbons=False,
        debug=False,
        xp_scale=2.0,
    )

    flags = build_flags(args)

    assert flags.no_shuffle is True
    assert flags.standard_treasure is True
    assert flags.boss_shuffle is True
    assert flags.new_items is True
    assert flags.scale_levels == 0.5


def test_canonical_json_hash_is_key_order_independent():
    first = {"b": 2, "a": 1}
    second = {"a": 1, "b": 2}

    assert canonical_json_sha256(first) == canonical_json_sha256(second)
    assert canonical_json_sha256(first) == hashlib.sha256(b'{"a":1,"b":2}').hexdigest()


def test_trace_summary_is_stable():
    placements = [{"source": "king", "reward": "bridge"}]
    trace = {
        "checkpoints": [
            {"name": "data_loaded", "enemies": 10},
            {"name": "placements", "placements": placements},
            {"name": "vehicle_starts", "ship": {"x": 1, "y": 2}},
        ],
        "patch_sets": [{"count": 1, "total_bytes": 2, "entries": [{"offset": 1, "length": 2, "sha256": "x"}]}],
    }

    summary = trace_summary(trace)

    assert summary["placement_count"] == 1
    assert summary["placement_sha256"] == canonical_json_sha256(placements)
    assert summary["patch_count"] == 1
    assert summary["patch_total_bytes"] == 2
    assert summary["vehicle_starts"] == {"ship": {"x": 1, "y": 2}}


def test_asset_manifest_covers_randomizer_inputs():
    assets = asset_manifest()

    assert "data/KeyItemPlacement.tsv" in assets
    assert "data/TextUpdates.tsv" in assets
    assert "patches/DataPointerConsolidation.ips" in assets
    assert "scripts/0x1388_Chest.script" in assets
    assert "asp/KeyItemSolvingShip.lp" in assets
    assert len(assets) > 50


def test_randomizer_result_metadata():
    flags = Flags()
    rom_data = b"test rom"
    result = RandomizerResult(
        rom_data=rom_data,
        seed="seed",
        flags=flags,
        base_rom_sha256=hashlib.sha256(b"base").hexdigest(),
    )

    metadata = result.to_metadata()
    assert metadata["seed"] == "seed"
    assert metadata["flags"]["scale_levels"] == 1.0
    assert metadata["flags_encoded"] == "KSTGB10"
    assert metadata["rom_sha256"] == hashlib.sha256(rom_data).hexdigest()
    assert metadata["rom_size"] == len(rom_data)
    assert "trace" not in metadata
    json.dumps(metadata)
