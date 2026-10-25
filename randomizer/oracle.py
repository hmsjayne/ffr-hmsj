#  Copyright 2026 HMS Jayne contributors
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""Run one randomizer case and emit a deterministic manifest.

This is the Python side of the future cross-language oracle. It is deliberately
separate from the interactive entry points so tests and the TypeScript parity
runner can rely on a stable interface.
"""

import argparse
import hashlib
import json
import platform
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from ips_util import Patch

from randomizer.api import randomize_rom
from randomizer.options import ALGORITHM_VERSION, DEFAULT_XP_RATE_PERCENT, RandomizerOptions
from randomizer.progress import PrintProgressReporter
from randomizer.seed import normalize_seed

REPO_ROOT = Path(__file__).resolve().parents[1]

ASSET_PATTERNS = (
    "data/*.tsv",
    "patches/*.ips",
    "scripts/*.script",
    "asp/*.lp",
    "static/seed_data.toml",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def asset_manifest(root: Path = REPO_ROOT) -> dict[str, str]:
    """Return a content hash for every input asset the randomizer reads."""
    paths = []
    for pattern in ASSET_PATTERNS:
        paths.extend(root.glob(pattern))
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(paths)
    }


def package_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def canonical_json_sha256(value) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _checkpoint_data(checkpoint: dict | None) -> dict | None:
    if checkpoint is None:
        return None
    return {key: value for key, value in checkpoint.items() if key != "name"}


def trace_summary(trace: dict | None) -> dict:
    """Return compact, stable values for a golden manifest."""
    if trace is None:
        return {}

    checkpoints = {
        checkpoint["name"]: checkpoint
        for checkpoint in trace.get("checkpoints", [])
    }
    placements = checkpoints.get("placements", {}).get("placements", [])
    patch_sets = trace.get("patch_sets", [])
    patch_entries = patch_sets[-1]["entries"] if patch_sets else []

    return {
        "data_loaded": _checkpoint_data(checkpoints.get("data_loaded")),
        "placement_count": len(placements),
        "placement_sha256": canonical_json_sha256(placements),
        "vehicle_starts": _checkpoint_data(checkpoints.get("vehicle_starts")),
        "patch_count": len(patch_entries),
        "patch_total_bytes": sum(entry["length"] for entry in patch_entries),
        "patch_manifest_sha256": canonical_json_sha256(patch_entries),
    }


def build_ips(base_rom: bytes, randomized_rom: bytes) -> bytes:
    return Patch.create(base_rom, randomized_rom).encode()


def build_options(args: argparse.Namespace) -> RandomizerOptions:
    return RandomizerOptions(
        shuffle_key_items=not args.no_shuffle,
        randomize_shops=not args.standard_shops,
        randomize_treasure=not args.standard_treasure,
        randomize_starting_gear=not args.default_start_gear,
        randomize_bosses=not args.default_bosses,
        new_item_distribution=args.new_items,
        fiend_ribbons=args.fiend_ribbons,
        xp_rate_percent=args.xp_rate,
        debug=args.debug,
    )


def run_case(rom_path: Path, seed: str, options: RandomizerOptions, progress=None,
             data_source=None) -> tuple[dict, bytes, bytes]:
    """Run one case and return (manifest, randomized_rom, ips_patch)."""
    seed = normalize_seed(seed)
    rom_bytes = rom_path.read_bytes()
    result = randomize_rom(rom_bytes, seed, options, data_source=data_source,
                           collect_trace=True, progress=progress)
    ips_data = build_ips(rom_bytes, result.rom_data)

    manifest = {
        "schema_version": 2,
        "algorithm_version": ALGORITHM_VERSION,
        "environment": {
            "python": platform.python_version(),
            "clingo": package_version("clingo"),
            "ips_util": package_version("ips-util"),
        },
        "input": {
            "rom_name": rom_path.name,
            "rom_sha256": hashlib.sha256(rom_bytes).hexdigest(),
            "rom_size": len(rom_bytes),
        },
        "seed": seed,
        "options": options.to_dict(),
        "options_short": options.short_code(),
        "rom": {
            "sha256": result.rom_sha256,
            "size": result.rom_size,
        },
        "ips": {
            "sha256": hashlib.sha256(ips_data).hexdigest(),
            "size": len(ips_data),
        },
        "assets": asset_manifest(),
        "trace": result.trace.to_dict() if result.trace is not None else None,
    }
    return manifest, result.rom_data, ips_data


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run one HMS Jayne randomizer case")
    parser.add_argument("--rom", required=True, type=Path, help="Path to a clean Dawn of Souls ROM")
    parser.add_argument("--seed", required=True, help="Seed string")
    parser.add_argument("--out", type=Path, help="Write the randomized ROM here")
    parser.add_argument("--ips-out", type=Path, help="Write the IPS patch here")
    parser.add_argument("--trace", type=Path, help="Write the JSON manifest here")
    parser.add_argument("--verbose", action="store_true", help="Show randomizer progress output")

    parser.add_argument("--no-shuffle", action="store_true", help="Do not shuffle key items")
    parser.add_argument("--standard-shops", action="store_true", help="Do not randomize shops")
    parser.add_argument("--standard-treasure", action="store_true", help="Do not randomize treasure")
    parser.add_argument("--default-start-gear", action="store_true", help="Keep vanilla starting gear")
    parser.add_argument("--default-bosses", action="store_true", help="Keep vanilla Fiend fights")
    parser.add_argument("--new-items", action="store_true", help="Use the new item distribution")
    parser.add_argument("--fiend-ribbons", action="store_true", help="Force Fiend ribbon drops")
    parser.add_argument("--debug", action="store_true", help="Enable debug randomizer behavior")
    parser.add_argument("--xp-rate", type=int, default=DEFAULT_XP_RATE_PERCENT,
                        help="Level-up speed percentage (150 = 1.5x normal speed)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        options = build_options(args)
        progress = PrintProgressReporter(file=sys.stderr) if args.verbose else None
        manifest, randomized_rom, ips_data = run_case(args.rom, args.seed, options, progress)
    except Exception as exc:  # noqa: BLE001 - CLI should report a clean error
        print(f"oracle: {exc}", file=sys.stderr)
        return 1

    if args.out is not None:
        args.out.write_bytes(randomized_rom)
    if args.ips_out is not None:
        args.ips_out.write_bytes(ips_data)
    if args.trace is not None:
        args.trace.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
