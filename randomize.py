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
from random import sample

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

    base_patch = load_ips_files("data/FF1R_Base.ips")
    rom = rom.apply_patches(base_patch)

    encounters = rom.encounters

    small_monsters = tuple(rom.enemies.find_by_size(0))
    big_monsters = tuple(rom.enemies.find_by_size(1))
    shuffled = dict(zip(small_monsters, sample(small_monsters, len(small_monsters))))
    shuffled.update(zip(big_monsters, sample(big_monsters, len(big_monsters))))

    new_encounters = map(lambda encounter: shuffle_encounter(encounter, shuffled), encounters)
    rom = rom.with_new_encounters(new_encounters)

    for monster in big_monsters:
        print(f"{hex(monster)}: {rom.enemies.names[monster]}")

    # for encounter in encounters:
    #     if not encounter.is_soc():
    #         print_encounter(rom, encounter)
    # for index in range(len(new_encounters)):
    #     new_encounter = new_encounters[index]
    #     orig = encounters[index]
    #     print_encounter(rom, new_encounter, orig)
    # index = 0
    # for name in rom.enemies.names:
    #     print(f"{hex(index)}: {name}")
    #     index += 1
    # for index in range(0, 0x80):
    #     print(f"{hex(index)}: {rom.enemies.names[index]}")

    rom.write("ffr-dos.gba")


def shuffle_encounter(encounter, shuffled):
    # Don't shuffle boss or mini-boss encounters
    if encounter.config in [0x3, 0x4, 0x6]:
        return encounter
    # Also don't move the fight vs the pirates
    if encounter.group_1_id == 0xf:
        return encounter
    # Don't move DeathMachine... just... no
    if encounter.group_1_id == 0x76:
        return encounter

    return encounter.apply_shuffle(shuffled)


def print_encounter(rom, encounter, orig):
    names = rom.enemies.names

    if encounter.is_unrunnable:
        unrunnable = " (Unrunnable)"
    else:
        unrunnable = ""
    print(f"Encounter {ENCOUNTER_TYPES[encounter.config]} : {encounter.surprise_chance}{unrunnable}")
    if encounter.group_1_max_count > 0:
        print(f"\tMonster: #{hex(encounter.group_1_id)} {names[encounter.group_1_id]}"
              f"x{encounter.group_1_min_count}-{encounter.group_1_max_count} (was {names[orig.group_1_id]})")
    if encounter.group_2_id != 0xff and encounter.group_2_max_count > 0:
        print(f"\tMonster: #{hex(encounter.group_2_id)} {names[encounter.group_2_id]}"
              f"x{encounter.group_2_min_count}-{encounter.group_2_max_count} (was {names[orig.group_2_id]})")
    if encounter.group_3_id != 0xff and encounter.group_3_max_count > 0:
        print(f"\tMonster: #{hex(encounter.group_3_id)} {names[encounter.group_3_id]}"
              f"x{encounter.group_3_min_count}-{encounter.group_3_max_count} (was {names[orig.group_3_id]})")
    if encounter.group_4_id != 0xff and encounter.group_4_max_count > 0:
        print(f"\tMonster: #{hex(encounter.group_4_id)} {names[encounter.group_4_id]}"
              f"x{encounter.group_4_min_count}-{encounter.group_4_max_count} (was {names[orig.group_4_id]})")


if __name__ == "__main__":
    main(sys.argv[1:])
