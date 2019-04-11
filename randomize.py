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
import copy
from argparse import ArgumentParser
from random import seed, randint

from doslib.event import EventTextBlock, EventTable
from doslib.eventbuilder import EventBuilder
from doslib.gen.classes import JobClass
from doslib.maps import Maps, TreasureChest, ItemChest
from doslib.rom import Rom
from ffr.flags import Flags
from ffr.keyitemsolver import solve_key_item_placement
from ffr.spellshuffle import SpellShuffle
from ffr.treasures import treasure_shuffle
from ipsfile import load_ips_files
from stream.output import Output

BASE_PATCHES = [
    "data/DataPointerConsolidation.ips",
    "data/ImprovedEquipmentStatViewing.ips",
    "data/NoEscape.ips",
    "data/RunningChange.ips",
    "data/StatusScreenExpansion.ips",
    "data/SpellLevelFix.ips"
]


def randomize(rom_path: str, flags: Flags, rom_seed: str):
    rom = Rom(rom_path)

    if rom_seed is None:
        rom_seed = hex(randint(0, 0xffffffff))

    seed(rom_seed)

    patches_to_load = BASE_PATCHES
    if flags.encounters is not None:
        patches_to_load.append("data/FF1EncounterToggle.ips")
    if flags.default_party is not None:
        patches_to_load.append("data/RandomDefault.ips")

    base_patch = load_ips_files(*patches_to_load)
    rom = rom.apply_patches(base_patch)

    event_text_block = EventTextBlock(rom)
    event_text_block.shrink()
    rom = event_text_block.pack(rom)

    rom = enable_free_airship(rom)
    rom = enable_generous_lukahn(rom)

    if flags.key_item_shuffle is not None:
        rom = shuffle_key_items(rom)

    if flags.magic is not None:
        shuffle_maigc = SpellShuffle(rom)
        rom = shuffle_maigc.write(rom)

    maps = Maps(rom)
    rom = maps.write(rom)

    if flags.treasures is not None:
        rom = treasure_shuffle(rom)

    if flags.debug is not None:
        class_stats_stream = rom.open_bytestream(0x1E1354, 96)
        class_stats = []
        while not class_stats_stream.is_eos():
            class_stats.append(JobClass(class_stats_stream))

        class_out_stream = Output()
        for job_class in class_stats:
            # Set the starting weapon and armor for all classes to something
            # very fair and balanced: Masamune + Diamond Armlet. :)
            job_class.weapon_id = 0x28
            job_class.armor_id = 0x0e

            # Write the (very balanced) new data out
            job_class.write(class_out_stream)
        rom = rom.apply_patch(0x1E1354, class_out_stream.get_buffer())

    rom.write("ffr-dos-" + rom_seed + ".gba")


def enable_free_airship(rom: Rom) -> Rom:
    map_init_events = EventTable(rom, 0x7050, 0xD3)
    main_events = EventTable(rom, 0x7788, 0xbb7, base_event_id=0x1388)

    # Build a new event (that will replace the soldiers in Coneria that usually bring you to the King.)
    event = EventBuilder() \
        .add_flag("garland_unlocked", 0x28) \
        .add_flag("show_airship", 0x15) \
        .add_label("init_world_map", map_init_events.get_addr(0)) \
        .set_flag("garland_unlocked", 0x0) \
        .set_flag("show_airship", 0x0) \
        .jump_to("init_world_map") \
        .event_end() \
        .get_event()

    # Write the new event over the old one.
    coneria_soldiers_event_id = 0x138C
    rom = rom.apply_patch(Rom.pointer_to_offset(main_events.get_addr(coneria_soldiers_event_id)), event)

    # Then, change the pointer of the world map init event script to point to ours,
    # so it runs as soon as the game starts.
    world_map_init_patch = Output()
    world_map_init_patch.put_u32(main_events.get_addr(coneria_soldiers_event_id))
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
    
    item_data = {
        "bridge": ('flag',0x02),
        "ship": ('flag', 0x05),
        "canal": ('flag', 0x0b),
        "earth": ('flag', 0x11),
        "fire": ('flag', 0x13),
        "water": ('flag', 0x1d),
        "air": ('flag', 0x22),
        "lute": ('item', 0x00),
        "crown": ('item', 0x01),
        "crystal": ('item', 0x02),
        "jolt_tonic": ('item', 0x03),
        "key": ('item', 0x04),
        "nitro_powder": ('item', 0x05),
        "adamant": ('item', 0x06),
        "slab": ('item', 0x07),
        "ruby": ('item', 0x08),
        "rod": ('item', 0x09),
        "levistone" : ('item', 0x0a),
        "chime": ('item',0x0b),
        "tail": ('item',0x0c),
        "cube": ('item', 0x0d),
        "bottle": ('item',0x0e),
        "oxyale": ('item',0x0f),
        "canoe": ('item', 0x10),
        "excalibur": ('item', 0x11),
        "gear": ('item', 0xFF),
    }
    
    item_sprite = {
        "bridge": 0x22, #King
        "lute": 0x00, #Princess Sarah
        "ship": 0x45,
        "canal": 0x3B,
        "earth": 0x51,
        "fire": 0x52,
        "water": 0x50,
        "air": 0x4F,
        "crown": 0x94, #Black Wizard (Black)
        "crystal": 0x47,
        "jolt_tonic": 0x37,
        "key": 0x31,
        "nitro_powder": 0x0D, #Soldier
        "adamant": 0x59,
        "slab": 0x1B, #Mermaid
        "ruby": 0x58, #The Ruby Sprite
        "rod": 0x39,
        "levistone": 0x57,
        "chime": 0x21,
        "tail": 0x25, #A Bat - any better ideas?
        "cube": 0x2B, #Sadly, no 0x9S exists
        "bottle": 0x44,
        "oxyale": 0x29,
        "canoe": 0x38,
        "excalibur": 0x3C,
        "gear": 0xFF
    }
    
    location_event_ids = {
        "lich": 0x13B3,
        "kary": 0x13A8,
        "kraken": 0x13A3,
        "tiamat": 0x13BB,
        "sara": 0x13A7,
        "king": 0x138B, #This is also, like, fighting Garland and stuff. It big.
        "bikke": 0x13B5,
        "marsh": 0x1398,
        "locked_cornelia": 0x13AD,
        "vampire": 0x13B7,
        "sarda": 0x13B8,
        "ice": 0x139F,
        "caravan": 0xFFFF,
        "astos": 0x1390,
        "matoya": 0x1391,
        "elf": 0x139A,
        "ordeals": 0x13AD,
        "waterfall": 0x13BD,
        "fairy": 0x138F,
        "mermaids": 0x13B4,
        "lefien": 0x1395,
        "smith": 0x139D,
        "lukahn": 0x1394,
        "sky2": 0x138D,
        "desert": 0xFFFF,
    }
    
    #This one's a *little* hacky - if it has 1 
    location_map_objects = {
        "lich": [(0x05,10)],
        "kary": [(0x2E,0)],
        "kraken": [(0x17,0)],
        "tiamat": [(0x60,0)],
        "sara": [(0x1F,6),(0x39,3)],
        "king": [(0x39,2)],
        "bikke": [(0x62,2)],
        "marsh": [(0x5B,5,0)],
        "locked_cornelia": [(0x38,2,2)],
        "vampire": [(0x03,1,0)],
        "sarda": [(0x37,0)],
        "ice": [(0x44,0)],
        "caravan": [(0x73,0)],
        "astos": [(0x58,0)],
        "matoya": [(0x61,4)],
        "elf": [(0x06,7)],
        "ordeals": [(0x4F,8,0)],
        "waterfall": [(0x53,0)],
        "fairy": [(0x47,11)],
        "mermaids": [(0x1E,0,12)],
        "lefien": [(0x70,11)],
        "smith": [(0x57,4)],
        "lukahn": [(0x2F,13)],
        "sky2": [(0x5D,0)],
        "desert": [None]
    }

    #Chime Lupa-ian is 0xB
    
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
    
    locations = Maps(rom)
    
    for s in key_item_locations:
        replace_item_event(item_data[s.item],location_event_id[s.location])
        replace_map_sprite(item_sprite[s.item],location_map_objects[s.location])
        print(s.location)
        
    #print(f"KI solution: {key_item_locations}")

    return rom


def main() -> int:
    parser = ArgumentParser(description="Final Fantasy Dawn of Souls Randomizer")
    parser.add_argument("rom", metavar="ROM file", type=str, help="The ROM file to randomize.")
    parser.add_argument("--seed", dest="seed", nargs=1, type=str, action="append", help="Seed value to use")
    parser.add_argument("--flags", dest="flags", nargs=1, type=str, action="append", required=True, help="Flags")
    parsed = parser.parse_args()

    # Ensure there's at most 1 seed.
    if parsed.seed is not None:
        seed_list = parsed.seed[0]
        if len(seed_list) > 1:
            parser.error("pass at most 1 value with --seed")
            return -1
        seed_value = seed_list[0]
    else:
        seed_value = None

    # It's possible to pass multiple --flags parameters, so collect them together and parse them.
    collected_flags = ""
    for flags in parsed.flags:
        collected_flags += f" {flags[0]}"
    flags = Flags(collected_flags)

    randomize(parsed.rom, flags, seed_value)
    return 0


if __name__ == "__main__":
    main()