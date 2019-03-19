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

import array
import sys

# Global to hold the ROM data (for now)
from ffa.rom import Rom
from ffa.text import text_to_ascii, encode_text

rom: Rom


# Simple routine to convert a memory address to an index into the ROM.
def addr_to_rom(addr):
    return addr - 0x8000000


# Looks up the starting memory address of an event given its ID
def lookup_event(id):
    if (id >= 0x0 and id <= 0xD3):
        lut_id_offset = 0x0
        lut_base = 0x08007050
    elif (id >= 0xFA0 and id <= 0xFAA):
        lut_id_offset = 0xFA0
        lut_base = 0x08007900
    elif id >= 0x1388 and id <= 0x1F3F:
        lut_id_offset = 0x1388
        lut_base = 0x08007788
    elif id >= 0x1F40 and id <= 0x202F:
        lut_id_offset = 0x1F40
        lut_base = 0x080073A0
    elif id >= 0x2328 and id <= 0x2403:
        lut_id_offset = 0x2328
        lut_base = 0x08006A98
    else:
        raise ValueError("Event id invalid: " + hex(id))

    # This is the address of the pointer in the LUT
    lut_addr = addr_to_rom(((id - lut_id_offset) * 4) + lut_base)
    # Since it's stored little endian, we only really need the
    # first two bytes.
    return addr_to_rom(array.array("I", rom[lut_addr:lut_addr + 4])[0])


def lookup_event_string(string_id):
    addr = 0x211770 + (string_id * 4)
    return addr_to_rom(array.array("I", rom[addr:addr + 4])[0])


def decompile(addr):
    working = dict()
    jumps = []

    last_cmd = -1
    while last_cmd != 0:
        # Name some things (for readability)
        cmd = rom[addr]
        cmd_len = rom[addr + 1]

        cmd_str = ""
        for i in range(cmd_len):
            cmd_str = cmd_str + hex(rom[addr + i]) + " "

        # Check to see if it's a branch, if it is we may want to
        # decompile it as well.
        if cmd == 0x0c:
            # Jump command
            jump_target = addr_to_rom(array.array("I", rom[addr + 4:addr + 8])[0])
            jumps.append(jump_target)
        elif cmd == 0x2d and cmd_len == 0x8:
            # 0x2d variant with alternate
            jump_target = addr_to_rom(array.array("I", rom[addr + 4:addr + 8])[0])
            jumps.append(jump_target)
        elif cmd == 0x48:
            # Another jump command
            jump_target = addr_to_rom(array.array("I", rom[addr + 4:addr + 8])[0])
            jumps.append(jump_target)
        elif cmd == 0x5:
            event_string_id = array.array("H", rom[addr + 2:addr + 4])[0]
            str_addr = lookup_event_string(event_string_id)
            cmd_str += f"\nText {hex(event_string_id)}:\n{text_to_ascii(rom.find_string(str_addr))}"

        working[addr] = cmd_str

        last_cmd = rom[addr]
        addr = addr + rom[addr + 1]

    for jump in jumps:
        if jump not in working:
            working.update(decompile(jump))

    return working


def main(argv):
    if len(argv) != 2:
        raise ValueError("Please pass ROM path and event ID parameters")

    global rom
    rom = Rom(argv[0])

    if argv[1].startswith("0x"):
        event_id = int(argv[1], 0)
    else:
        event_id = int(argv[1], 16)

    # Decompile the event in a function so it can recurse.
    addr = lookup_event(event_id)
    event_code = decompile(addr)

    for key, value in sorted(event_code.items(), key=lambda x: x[0]):
        print("{:x}: {}".format(key, value))


if __name__ == "__main__":
    main(sys.argv[1:])
