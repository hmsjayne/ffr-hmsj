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
from event.e2s import disassemble_event, lookup_event, offset_to_addr


def main():
    parser = ArgumentParser(description="Final Fantasy: Dawn of Souls Event->Script")
    parser.add_argument("rom_file", type=FileType('rb', 0), help="The ROM file to read.")
    parser.add_argument("--event", dest="event", type=str, help="Event to disassemble")
    parser.add_argument("--all", dest="all_events", action="store_true", help="Disassemble all events")
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

        working, labels = disassemble_event(rom, event_id)
        for offset, cmd in sorted(working.items(), key=lambda x: x[0]):
            addr = offset_to_addr(offset)
            if addr in labels:
                print(f"{labels[addr]}:")
            print(cmd)
    elif parsed.all_events:
        for event_id in range(0x0, 0x2030):
            try:
                addr = lookup_event(rom, event_id)
            except ValueError:
                # Since there are gaps, just ignore when we try to disassemble an invalid event
                continue

            print(f"begin script={hex(event_id)}")
            working, labels = disassemble_event(rom, addr=addr)
            for offset, cmd in sorted(working.items(), key=lambda x: x[0]):
                addr = offset_to_addr(offset)
                if addr in labels:
                    print(f"\t{labels[addr]}:")
                print(f"\t{cmd}")


if __name__ == "__main__":
    main()
