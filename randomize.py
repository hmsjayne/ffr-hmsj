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

import random
from argparse import ArgumentParser, FileType

from randomizer.flags import Flags
from randomizer.randomize import randomize
from ips_util import Patch


def main() -> int:
    parser = ArgumentParser(description="HMS Janye: Final Fantasy I: Dawn of Souls Randomizer")
    parser.add_argument("rom_file", type=FileType('rb', 0), help="The ROM file to randomize.")
    parser.add_argument("--seed", dest="seed", nargs=1, type=str, help="Seed value to use")
    parser.add_argument("--xp-scale", dest="exp_mult", type=float,
                        help="Experience modifier: 1=level gain; 2=gain levels twice as fast; "
                             "0.5=gain levels half as fast")

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
    parser.add_argument("--patch", dest="patch", action="store_true", help="Generate a patch file (ips) instead of a "
                                                                           "new rom")

    parsed = parser.parse_args()

    # Ensure there's at most 1 seed.
    if parsed.seed is not None:
        seed_value = parsed.seed.pop()
        if len(seed_value) > 10:
            seed_value = seed_value[0:10]
    else:
        rng = random.Random()
        seed_value = hex(rng.randint(0, 0xffffffff))[2:]

    # Convert from command line flags to internal
    flags = Flags(parsed)

    rom_file = parsed.rom_file
    rom_data = bytearray(rom_file.read())
    rom_file.close()

    base_name = rom_file.name.replace(".gba", "")
    randomized_rom = randomize(rom_data, seed_value, flags)

    if not parsed.patch:
        output_name = f"{base_name}_{flags.encode()}_{seed_value}.gba"
        with open(output_name, "wb") as output:
            output.write(randomized_rom)
    else:
        output_name = f"{base_name}_{flags.encode()}_{seed_value}.ips"
        patch = Patch.create(rom_data, randomized_rom)
        with open(output_name, "wb") as output:
            output.write(patch.encode())

    return 0


if __name__ == "__main__":
    main()
