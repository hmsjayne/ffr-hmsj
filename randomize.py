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

from doslib.etextblock import EventTextBlock
from doslib.rom import Rom
from ipsfile import load_ips_files
from stream.output import Output

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


def main(argv):
    rom = Rom(argv[0])

    if len(argv) > 1:
        rom_seed = argv[1]
    else:
        rom_seed = hex(randint(0, 0xffffffff))

    seed(seed)

    base_patch = load_ips_files(*BASE_PATCHES)
    rom = rom.apply_patches(base_patch)

    event_text_block = EventTextBlock(rom)
    event_text_block.shrink()
    patches = event_text_block.pack()

    rom = rom.apply_patch(0x211770, patches.lut)
    rom = rom.apply_patch(Rom.pointer_to_offset(event_text_block.lut[0]), patches.data)

    rom = enable_free_airship(rom)

    rom.write("ffr-dos-" + rom_seed + ".gba")


def enable_free_airship(rom: Rom) -> Rom:
    map_init_events = list(rom.get_lut(0x7050, 0xD3))
    main_events = rom.get_lut(0x7788, 0xbb7)

    # Move the airship's start location to right outside of Coneria.
    airship_start = Output()
    airship_start.put_u32(0x918)
    airship_start.put_u32(0x9e8)
    rom = rom.apply_patch(0x65280, airship_start.get_buffer())

    return rom

if __name__ == "__main__":
    main(sys.argv[1:])
