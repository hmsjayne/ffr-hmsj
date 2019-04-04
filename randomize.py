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

from doslib.ShopData import ShopData
from doslib.event import EventTextBlock, EventTable
from doslib.eventbuilder import EventBuilder
from doslib.rom import Rom
from ffr.keyitemsolver import solve_key_item_placement
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

    seed(rom_seed)

    base_patch = load_ips_files(*BASE_PATCHES)
    rom = rom.apply_patches(base_patch)

    event_text_block = EventTextBlock(rom)
    event_text_block.shrink()
    rom = event_text_block.pack(rom)

    rom = enable_free_airship(rom)
    rom = enable_generous_lukahn(rom)

    rom = shuffle_key_items(rom)

    # TODO: ...Something. Shuffle or whatever. At least they can be read and written out ;)
    shops = ShopData(rom)
    rom = shops.write(rom)

    rom.write("ffr-dos-" + rom_seed + ".gba")


def enable_free_airship(rom: Rom) -> Rom:
    map_init_events = EventTable(rom, 0x7050, 0xD3)
    main_events = EventTable(rom, 0x7788, 0xbb7, base_event_id=0x1388)

    # Build a new event (that will replace the soldiers in Coneria that usually bring you to the King.)
    event = EventBuilder() \
        .add_flag("garland_unlocked", 0x28) \
        .add_flag("show_airship", 0x15) \
        .add_label("init_world_map", map_init_events[0]) \
        .set_flag("garland_unlocked", 0x0) \
        .set_flag("show_airship", 0x0) \
        .jump_to("init_world_map") \
        .event_end() \
        .get_event()

    # Write the new event over the old one.
    coneria_soldiers_event_id = 0x138C
    rom = rom.apply_patch(Rom.pointer_to_offset(main_events[coneria_soldiers_event_id]), event)

    # Then, change the pointer of the world map init event script to point to ours,
    # so it runs as soon as the game starts.
    world_map_init_patch = Output()
    world_map_init_patch.put_u32(main_events[coneria_soldiers_event_id])
    rom = rom.apply_patch(0x7050, world_map_init_patch.get_buffer())

    # Finally, move the airship's start location to right outside of Coneria Castle.
    airship_start = Output()
    airship_start.put_u32(0x918)
    airship_start.put_u32(0x998)
    rom = rom.apply_patch(0x65280, airship_start.get_buffer())

    return rom


def enable_generous_lukahn(rom: Rom) -> Rom:
    # The "Give Canoe" Event (ID 0x1394) is normally on NPC 0xc (AKA, the "Canoe Sage").
    # Since their sprite is kind of generic, it would be easier for spotting them outside of
    # Crescent Lake if Lukahn was the one giving the item.
    event = EventBuilder() \
        .set_event_on_npc(0xd, 0x1394) \
        .get_event()

    return rom.apply_patch(0x90f8, event)


def shuffle_key_items(rom: Rom) -> Rom:
    key_item_locations = solve_key_item_placement(randint(0, 0xffffffff))

    # The Key items returned work like this. Suppose a Placement returned was
    # `Placement(item='oxyale', location='king')` this means that the "Oxyale" key item
    # should be found in the King of Cornelia location.
    #
    # This does *NOT* mean the King of Cornelia will give you Oxyale, rather, it means the NPC
    # that gives Oxyale (the Fairy) should be placed in the King's spot.
    #
    # Further, the Fairy in the King of Cornelia's spot, will be there at the start of the game, and
    # won't need to be rescued from the Bottle. It *does* mean that the Fairy won't provide Oxyale
    # until Garland is defeated and that NPC (or treasure) is itself rescued.

    print(f"KI solution: {key_item_locations}")

    return rom


if __name__ == "__main__":
    main(sys.argv[1:])
