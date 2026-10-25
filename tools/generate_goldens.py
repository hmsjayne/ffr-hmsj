#!/usr/bin/env python3
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

"""Generate the Python baseline manifest used by parity tests.

The base ROM is intentionally not stored in the repository. Pass its path
explicitly; the manifest records only hashes and compact traces.
"""

import argparse
import hashlib
import json
import platform
import sys
from dataclasses import dataclass, replace
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from randomizer.options import ALGORITHM_VERSION, DEFAULT_OPTIONS, RandomizerOptions
from randomizer.oracle import (
    asset_manifest,
    package_version,
    run_case,
    trace_summary,
)


@dataclass(frozen=True)
class GoldenCase:
    name: str
    seed: str
    options: dict


def case(name: str, seed: str, **overrides) -> GoldenCase:
    options = replace(DEFAULT_OPTIONS, **overrides)
    return GoldenCase(name=name, seed=seed, options=options.to_dict())


CASES = (
    case("default", "test"),
    case("default_alt_seed", "abc"),
    case("no_shuffle", "test", shuffle_key_items=False),
    case("standard_shops", "test", randomize_shops=False),
    case("standard_treasure", "test", randomize_treasure=False),
    case("default_start_gear", "test", randomize_starting_gear=False),
    case("default_bosses", "test", randomize_bosses=False),
    case("new_items", "test", new_item_distribution=True),
    case("fiend_ribbons", "test", fiend_ribbons=True),
    case("xp_50", "test", xp_rate_percent=50),
    case("xp_200", "test", xp_rate_percent=200),
    case(
        "all_standard",
        "test",
        shuffle_key_items=False,
        randomize_shops=False,
        randomize_treasure=False,
        randomize_starting_gear=False,
        randomize_bosses=False,
    ),
    case(
        "all_features",
        "test",
        new_item_distribution=True,
        fiend_ribbons=True,
        xp_rate_percent=200,
    ),
    case("max_seed", "ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"),
    case("seed_with_spaces", "Voyage of the Cactuar"),
)


def build_manifest(rom_path: Path) -> dict:
    base_rom = rom_path.read_bytes()
    results = []
    for golden_case in CASES:
        options = RandomizerOptions(**golden_case.options)

        manifest, _randomized_rom, _ips_data = run_case(rom_path, golden_case.seed, options)

        results.append({
            "name": golden_case.name,
            "seed": golden_case.seed,
            "options": golden_case.options,
            "options_short": options.short_code(),
            "rom_sha256": manifest["rom"]["sha256"],
            "rom_size": manifest["rom"]["size"],
            "ips_sha256": manifest["ips"]["sha256"],
            "ips_size": manifest["ips"]["size"],
            "trace": trace_summary(manifest["trace"]),
        })

    return {
        "schema_version": 2,
        "algorithm_version": ALGORITHM_VERSION,
        "environment": {
            "python": platform.python_version(),
            "clingo": package_version("clingo"),
            "ips_util": package_version("ips-util"),
        },
        "base_rom": {
            "name": rom_path.name,
            "sha256": hashlib.sha256(base_rom).hexdigest(),
            "size": len(base_rom),
        },
        "assets": asset_manifest(),
        "cases": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate HMS Jayne golden baseline")
    parser.add_argument("--rom", required=True, type=Path, help="Path to a clean Dawn of Souls ROM")
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "tests" / "golden" / "rom_hashes.json",
        help="Output manifest path",
    )
    args = parser.parse_args(argv)

    if not args.rom.is_file():
        print(f"generate_goldens: ROM not found: {args.rom}", file=sys.stderr)
        return 1

    manifest = build_manifest(args.rom)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"Wrote {args.out} ({len(manifest['cases'])} cases)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
