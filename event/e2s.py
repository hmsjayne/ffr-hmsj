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

import array
from argparse import ArgumentParser

from doslib.rom import Rom


# Simple routine to convert a memory address to an index into the ROM.
def addr_to_rom(addr):
    return addr - 0x8000000


# Looks up the starting memory address of an event given its ID
def lookup_event(rom: Rom, event_id: int):
    if 0x0 <= event_id <= 0xD3:
        lut_id_offset = 0x0
        lut_base = 0x08007050
    elif 0xFA0 <= event_id <= 0xFAA:
        lut_id_offset = 0xFA0
        lut_base = 0x08007900
    elif 0x1388 <= event_id <= 0x13CC:
        lut_id_offset = 0x1388
        lut_base = 0x08007788
    elif 0x1F40 <= event_id <= 0x202F:
        lut_id_offset = 0x1F40
        lut_base = 0x080073A0
    elif 0x2328 <= event_id <= 0x2404:
        lut_id_offset = 0x2328
        lut_base = 0x08006A98
    else:
        raise ValueError("Event id invalid: " + hex(event_id))

    # This is the address of the pointer in the LUT
    lut_addr = addr_to_rom(((event_id - lut_id_offset) * 4) + lut_base)
    # Since it's stored little endian, we only really need the
    # first two bytes.
    return addr_to_rom(array.array("I", rom.rom_data[lut_addr:lut_addr + 4])[0])


def disassemble(rom: Rom, addr: int) -> dict:
    rom_data = rom.rom_data
    working = dict()

    if addr < 0 or addr > len(rom_data):
        print(f"Invalid address: {hex(addr)}")
        return working

    last_cmd = -1
    while last_cmd != 0:
        # Name some things (for readability)
        cmd = rom_data[addr]
        cmd_len = rom_data[addr + 1]

        full_cmd = rom_data[addr:addr + cmd_len]
        if cmd not in working:
            working[cmd] = []
        working[cmd].append(full_cmd)

        last_cmd = cmd
        addr = addr + cmd_len

    return working


def disassemble_event(rom: Rom, event_id: int) -> dict:
    # Decompile the event in a function so it can recurse.
    addr = lookup_event(rom, event_id)
    return disassemble(rom, addr)


def main():
    parser = ArgumentParser(description="Final Fantasy: Dawn of Souls Event->Script")
    parser.add_argument("rom", metavar="ROM file", type=str, help="ROM source file")
    parser.add_argument("--event", dest="event", type=str, help="Event to disassemble")
    parsed = parser.parse_args()

    # Opening the ROM is simple.
    rom = Rom(parsed.rom)

    # The event id is a bit trickier. The parser won't recognize hex values, so we need to accept it as a
    # string and convert it ourselves.
    if parsed.event.startswith("0x"):
        event_id = int(parsed.event, 16)
    else:
        event_id = int(parsed.event)

    disassemble_event(rom, event_id)


if __name__ == "__main__":
    main()
