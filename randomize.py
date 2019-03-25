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
from random import seed, randint

from ffa.rom import Rom
from ipsfile import load_ips_files

BASE_PATCHES = [
    "data/DataPointerConsolidation.ips",
    "data/FF1EncounterToggle.ips",
    "data/ImprovedEquipmentStatViewing.ips",
    "data/NoEscape.ips",
    "data/RandomDefault.ips",
    "data/RunningChange.ips",
    "data/StatusScreenExpansion.ips",
    "data/SpellLevelFix.ips"
]

ENCOUNTER_TYPES = {
    0x0: "1-9 Small monsters (3x3)",
    0x1: "1-2 Large, 1-6 Small",
    0x2: "1-4 Large",
    0x3: "1 Fiend-size monster",
    0x4: "1 Small miniboss",
    0x5: "1-9 Small land+flying monsters",
    0x6: "Dawn of Souls boss"
}


def main(argv):
    rom = Rom(argv[0])

    if len(argv) > 1:
        rom_seed = argv[1]
    else:
        rom_seed = hex(randint(0, 0xffffffff))

    seed(seed)

    base_patch = load_ips_files(*BASE_PATCHES)

    rom = rom.apply_patches(base_patch)
    rom.write("ffr-dos-" + rom_seed + ".gba")


def encounter_p(rom, index, encounter):
    names = rom.enemies.names

    if encounter.is_unrunnable:
        unrunnable = " (Unrunnable)"
    else:
        unrunnable = ""
    print_index = f"#{hex(index)}" if index is not None else ""
    print(f"Encounter {print_index} {ENCOUNTER_TYPES[encounter.config]} : {encounter.surprise_chance}{unrunnable}")
    if encounter.group_1_max_count > 0:
        print(f"\tMonster: #{hex(encounter.group_1_id)} {names[encounter.group_1_id]}"
              f"x{encounter.group_1_min_count}-{encounter.group_1_max_count}")
    if encounter.group_2_id != 0xff and encounter.group_2_max_count > 0:
        print(f"\tMonster: #{hex(encounter.group_2_id)} {names[encounter.group_2_id]}"
              f"x{encounter.group_2_min_count}-{encounter.group_2_max_count}")
    if encounter.group_3_id != 0xff and encounter.group_3_max_count > 0:
        print(f"\tMonster: #{hex(encounter.group_3_id)} {names[encounter.group_3_id]}"
              f"x{encounter.group_3_min_count}-{encounter.group_3_max_count}")
    if encounter.group_4_id != 0xff and encounter.group_4_max_count > 0:
        print(f"\tMonster: #{hex(encounter.group_4_id)} {names[encounter.group_4_id]}"
              f"x{encounter.group_4_min_count}-{encounter.group_4_max_count}")


if __name__ == "__main__":
    main(sys.argv[1:])
