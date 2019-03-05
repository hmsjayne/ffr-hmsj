#!/usr/bin/env python3

#  Copyright 2019 Nicole Borrelli
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

import sys

from ffa.rom import open_rom, write_rom, load_monster_names

BASE_PATCHES = [
    "data/DataPointerConsolidation.ips",
    "data/FF1EncounterToggle.ips",
    "data/ImprovedEquipmentStatViewing.ips",
    "data/NoEscape.ips",
    "data/RandomDefault.ips",
    "data/RunningChange.ips",
    "data/StatusScreenExpansion.ips",
]


def main(argv):
    rom = open_rom(argv[0])

    # airship_patch = load_ips_files(*BASE_PATCHES)
    # rom = apply_patches(rom, airship_patch)

    names = load_monster_names(rom)
    for name in names:
        print(f"Monster: {name}")

    write_rom("ffr-dos.gba", rom)


if __name__ == "__main__":
    main(sys.argv[1:])
