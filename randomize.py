#!/usr/bin/env python3
#  Copyright 2020 Nicole Borrelli
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

from argparse import ArgumentParser, FileType
from pathlib import Path

from ips_util import Patch

from randomizer.api import randomize_rom
from randomizer.options import DEFAULT_XP_RATE_PERCENT, RandomizerOptions
from randomizer.progress import PrintProgressReporter
from randomizer.seed import generate_seed, normalize_seed
from randomizer.share import build_filename


def main() -> int:
    parser = ArgumentParser(description="HMS Janye: Final Fantasy I: Dawn of Souls Randomizer")
    parser.add_argument("rom_file", type=FileType('rb', 0), help="The ROM file to randomize.")
    parser.add_argument("--seed", dest="seed", type=str, help="Seed value to use")
    parser.add_argument("--xp-rate", dest="xp_rate", type=int, default=None,
                        help="Level-up speed percentage (100 = vanilla, 200 = twice as fast)")
    parser.add_argument("--xp-scale", dest="xp_scale", type=float, default=None,
                        help="Deprecated: level-up speed multiplier (2 = twice as fast)")

    parser.add_argument("--original-progression", dest="no_shuffle", action="store_true",
                        help="Do not shuffle key items")
    parser.add_argument("--standard-shops", dest="standard_shops", action="store_true",
                        help="Don't randomize the inventory of item, weapon, armor, or magic shops")
    parser.add_argument("--standard-treasure", dest="standard_treasure", action="store_true",
                        help="Don't randomize the contents of chests")
    parser.add_argument("--default-start-gear", dest="default_start_gear", action="store_true",
                        help="Don't generate new starting equipment for the classes")
    parser.add_argument("--default-boss-fights", dest="boss_shuffle", action="store_true",
                        help="Keep original Fiend fights")
    parser.add_argument("--new-items", dest="new_items", action="store_true",
                        help="Experimental Item Distribution")
    parser.add_argument("--fiend_ribbons", dest="fiend_ribbons", action="store_true",
                        help="Fiend 1's drop ribbons")
    parser.add_argument("--debug", dest="debug", action="store_true", help="Enable debugging")
    parser.add_argument("--patch", dest="patch", action="store_true",
                        help="Generate a patch file (ips) instead of a new rom")

    parsed = parser.parse_args()

    if parsed.xp_rate is not None and parsed.xp_scale is not None:
        parser.error("use either --xp-rate or --xp-scale, not both")
    if parsed.xp_scale is not None:
        if parsed.xp_scale <= 0:
            parser.error("--xp-scale must be greater than zero")
        xp_rate = round(parsed.xp_scale * 100)
    elif parsed.xp_rate is not None:
        xp_rate = parsed.xp_rate
    else:
        xp_rate = DEFAULT_XP_RATE_PERCENT

    try:
        options = RandomizerOptions(
            shuffle_key_items=not parsed.no_shuffle,
            randomize_shops=not parsed.standard_shops,
            randomize_treasure=not parsed.standard_treasure,
            randomize_starting_gear=not parsed.default_start_gear,
            randomize_bosses=not parsed.boss_shuffle,
            new_item_distribution=parsed.new_items,
            fiend_ribbons=parsed.fiend_ribbons,
            xp_rate_percent=xp_rate,
            debug=parsed.debug,
        )
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))

    try:
        seed_value = normalize_seed(parsed.seed) if parsed.seed else generate_seed()
    except ValueError as exc:
        parser.error(str(exc))

    rom_file = parsed.rom_file
    rom_data = bytearray(rom_file.read())
    rom_file.close()

    base_path = Path(rom_file.name)
    result = randomize_rom(rom_data, seed_value, options, progress=PrintProgressReporter())
    randomized_rom = result.rom_data

    extension = "ips" if parsed.patch else "gba"
    output_name = base_path.parent / build_filename(
        seed_value, options, base_name=base_path.stem, extension=extension
    )
    if not parsed.patch:
        output_name.write_bytes(randomized_rom)
    else:
        patch = Patch.create(rom_data, randomized_rom)
        output_name.write_bytes(patch.encode())

    return 0


if __name__ == "__main__":
    main()
