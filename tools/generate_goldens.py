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
import contextlib
import hashlib
import io
import json
import platform
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from randomizer.flags import Flags
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
    flags: dict


def case(
    name: str,
    seed: str,
    *,
    no_shuffle: bool = False,
    standard_shops: bool = False,
    standard_treasure: bool = False,
    default_start_gear: bool = False,
    default_bosses: bool = False,
    new_items: bool = False,
    fiend_ribbons: bool = False,
    debug: bool = False,
    xp_scale: float | None = None,
) -> GoldenCase:
    flags = Flags()
    flags.no_shuffle = no_shuffle
    flags.standard_shops = standard_shops
    flags.standard_treasure = standard_treasure
    flags.default_start_gear = default_start_gear
    flags.boss_shuffle = default_bosses
    flags.new_items = new_items
    flags.fiend_ribbons = fiend_ribbons
    flags.debug = debug
    if xp_scale is not None:
        flags.scale_levels = 1.0 / xp_scale
    return GoldenCase(name=name, seed=seed, flags=dict(vars(flags)))


CASES = (
    case("default", "test"),
    case("default_alt_seed", "abc"),
    case("no_shuffle", "test", no_shuffle=True),
    case("standard_shops", "test", standard_shops=True),
    case("standard_treasure", "test", standard_treasure=True),
    case("default_start_gear", "test", default_start_gear=True),
    case("default_bosses", "test", default_bosses=True),
    case("new_items", "test", new_items=True),
    case("fiend_ribbons", "test", fiend_ribbons=True),
    case("xp_50", "test", xp_scale=0.5),
    case("xp_200", "test", xp_scale=2.0),
    case(
        "all_standard",
        "test",
        no_shuffle=True,
        standard_shops=True,
        standard_treasure=True,
        default_start_gear=True,
        default_bosses=True,
    ),
    case(
        "all_features",
        "test",
        new_items=True,
        fiend_ribbons=True,
        xp_scale=2.0,
    ),
    case("empty_seed", ""),
)


def build_manifest(rom_path: Path) -> dict:
    base_rom = rom_path.read_bytes()
    results = []
    for golden_case in CASES:
        flags = Flags()
        for key, value in golden_case.flags.items():
            setattr(flags, key, value)

        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            manifest, _randomized_rom, _ips_data = run_case(rom_path, golden_case.seed, flags)

        results.append({
            "name": golden_case.name,
            "seed": golden_case.seed,
            "flags": golden_case.flags,
            "flags_encoded": flags.encode(),
            "rom_sha256": manifest["rom"]["sha256"],
            "rom_size": manifest["rom"]["size"],
            "ips_sha256": manifest["ips"]["sha256"],
            "ips_size": manifest["ips"]["size"],
            "trace": trace_summary(manifest["trace"]),
        })

    return {
        "schema_version": 1,
        "algorithm_version": 1,
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
