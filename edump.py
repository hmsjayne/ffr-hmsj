#!/usr/bin/env python3

import array, sys

# Global to hold the ROM data (for now)
rom_data = bytes()

# Simple routine to convert a memory address to an index into the ROM.
def addr_to_rom(addr):
    return addr - 0x8000000

# Looks up the starting memory address of an event given its ID
def lookup_event(id):
    if (id >= 0x0 and id <= 0x100):
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
    return addr_to_rom(array.array("I", rom_data[lut_addr:lut_addr + 4])[0])

def decompile(addr):
    working = dict()
    jumps = []

    last_cmd = -1
    while last_cmd != 0:
        # Name some things (for readability)
        cmd = rom_data[addr]
        cmd_len = rom_data[addr + 1]

        cmd_str = ""
        for i in range(cmd_len):
            cmd_str = cmd_str + hex(rom_data[addr + i]) + " "
        working[addr] = cmd_str

        # Check to see if it's a branch, if it is we may want to
        # decompile it as well.
        if (cmd == 0x0c):
            # Jump command
            jump_target = addr_to_rom(array.array("I", rom_data[addr + 4:addr + 8])[0])
            jumps.append(jump_target)
        elif (cmd == 0x2d and cmd_len == 0x8):
            # 0x2d variant with alternate
            jump_target = addr_to_rom(array.array("I", rom_data[addr + 4:addr + 8])[0])
            jumps.append(jump_target)
        elif (cmd == 0x48):
            # Another jump command
            jump_target = addr_to_rom(array.array("I", rom_data[addr + 4:addr + 8])[0])
            jumps.append(jump_target)

        last_cmd = rom_data[addr]
        addr = addr + rom_data[addr + 1]

    for jump in jumps:
        if jump not in working:
            working.update(decompile(jump))

    return working

def main(argv):
    if len(argv) != 2:
        raise ValueError("Please pass ROM path and event ID parameters")

    with open(argv[0], "rb") as binary_file:
        global rom_data
        # Read the whole file at once
        rom_data = binary_file.read()

    if (argv[1].startswith("0x")):
        event_id = int(argv[1], 0)
    else:
        event_id = int(argv[1], 16)

    # Decompile the event in a function so it can recurse.
    addr = lookup_event(event_id)
    event_code = decompile(addr)

    for key, value in sorted(event_code.items(), key=lambda x: x[0]):
        print("{:x}: {}".format(key, value))

if __name__== "__main__":
  main(sys.argv[1:])
