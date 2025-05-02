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

from argparse import ArgumentParser, FileType

from doslib.rom import Rom
from event.consts import map_names
from event.e2s import disassemble_event, lookup_event, offset_to_addr, event_to_map_id


def do_disassemble_event(rom, event_id, event_name=None):
    if event_name is not None:
        print(f"; {event_name}")

    print(f"begin script={hex(event_id)}")
    working, labels = disassemble_event(rom, event_id)
    for offset, cmd in sorted(working.items(), key=lambda x: x[0]):
        addr = offset_to_addr(offset)
        if addr in labels:
            print(f"\t{labels[addr]}:")
        print(f"\t{cmd}")
    print("")


def do_dissassemble_events(rom, events: dict[int, str]):
    for event_id in sorted(events.keys()):
        try:
            addr = lookup_event(rom, event_id)
        except ValueError:
            # Since there are gaps, just ignore when we try to disassemble an invalid event
            continue

        if addr is None:
            continue

        do_disassemble_event(rom, event_id, events[event_id])
        print("")


def main():
    parser = ArgumentParser(description="Final Fantasy: Dawn of Souls Event->Script")
    parser.add_argument("rom_file", type=FileType('rb', 0), help="The ROM file to read.")
    parser.add_argument("--event", dest="event", type=str, help="Event to disassemble")
    parser.add_argument("--maps", dest="all_maps", action="store_true", help="Disassemble all map events")
    parser.add_argument("--core", dest="core_events", action="store_true", help="Disassemble core events")
    parser.add_argument("--battle", dest="battle_events", action="store_true", help="Disassemble battle events")
    parsed = parser.parse_args()

    # Opening the ROM is simple.
    rom_file = parsed.rom_file
    rom_data = bytearray(rom_file.read())
    rom_file.close()
    rom = Rom(rom_data)

    if parsed.event is not None:
        # The event id is a bit trickier. The parser won't recognize hex values, so we need to accept it as a
        # string and convert it ourselves.
        if parsed.event.startswith("0x"):
            event_id = int(parsed.event, 16)
        else:
            event_id = int(parsed.event)

        do_disassemble_event(rom, event_id)
        return

    if parsed.all_maps:
        for event_id in range(0x0, 0x7c):
            try:
                addr = lookup_event(rom, event_id)
            except ValueError:
                # Since there are gaps, just ignore when we try to disassemble an invalid event
                continue

            if addr is None:
                continue

            if event_id in map_names:
                event_name = f"Map initialization code for {map_names[event_id]}"
            else:
                event_name = None
            do_disassemble_event(rom, event_id, event_name)
            print("")

        # One special case for "maps"
        do_disassemble_event(rom, 0xfa6, "Bridge_Credits")
    if parsed.core_events:
        core_event_names = {
            0x1388: "Chest",
            0x138c: "Heard_Kings_Plight",
            0x138d: "Adamantite_obtaining",
            0x138e: "Airship_rises_from_Ryukahn_Desert",
            0x138f: "Fairy_gets_Oxyale",
            0x1391: "Giving_Crystal_Eye_to_Matoya",
            0x1393: "Nerrick_uses_Nitro_Powder",
            0x1394: "Receive_Canoe",
            0x1395: "Receive_Chime",
            0x1396: "Class_change",
            0x1398: "Crown_chest",
            0x139a: "Give_Jolt_Tonic_to_Healer",
            0x139c: "Use_Rod_in_Earth_B4",
            0x139d: "Give_Adamantite_to_Smyth",
            0x139f: "Levistone_obtaining",
            0x1399: "Feed_Star_Ruby_to_Titan",
            0x13a5: "Unne_deciphers_Rosetta_Stone",
            0x13a7: "Receive_Lute",
            0x13aa: "Rat_Tail_chest",
            0x13ad: "Nitro_Powder_chest",
            0x13b4: "Rosetta_Stone_chest",
            0x13B6: "Using_Sleeping_Bag",
            0x13b7: "Star_Ruby_chest",
            0x13b8: "Receive_Earth_Rod",
            0x13bd: "Robot_gives_Warp_Cube",
            0x1F49: "Cornelia_fountain",
            0x1f60: "Chancellor_of_Cornelia",
        }
        do_dissassemble_events(rom, core_event_names)
    if parsed.battle_events:
        core_event_names = {
            0x138b: "Confronting_Garland",
            0x1390: "Confronting_Astos",
            0x13a3: "Confronting_Kraken",
            0x13a4: "Confronting_Chaos",
            0x13a8: "Confronting_Marilith",
            0x13b3: "Confronting_Lich",
            0x13b5: "Confronting_Bikke",
            0x13bb: "Confronting_Tiamat",
            0x13Bc: "Confronting_Vampire",
        }
        do_dissassemble_events(rom, core_event_names)


if __name__ == "__main__":
    main()
