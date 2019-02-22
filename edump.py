#!/usr/bin/env python3

# Global to hold the ROM data (for now)
rom_data = bytes()

def lookup_event(id):
    print("ROM has len: " + str(len(rom_data)))
    if id >= 0x1388 and id <= 0x1F3F:
        lut_id_offset = 0x1388
        lut_base = 0x7788
    else:
        raise ValueError("Event id invalid: " + hex(id))

    # This is the address of the pointer in the LUT
    lut_addr = ((id - lut_id_offset) * 4) + lut_base
    # Since it's stored little endian, we only really need the
    # first two bytes.
    return (rom_data[lut_addr + 1] << 8) + rom_data[lut_addr]

def main():
    with open("ff-dos.gba", "rb") as binary_file:
        global rom_data
        # Read the whole file at once
        rom_data = binary_file.read()
    addr = lookup_event(0x138C)

    # Events start with a command, followed by a lengthself.
    # The important one is '0', for now, which is "end".
    # No processing is done to check for branches/jumps yetself.
    while rom_data[addr] != 0:
        cmd = ""
        for i in range(rom_data[addr + 1]):
            cmd = cmd + hex(rom_data[addr + i]) + " "
        print(hex(addr) + ": " + cmd)
        addr = addr + rom_data[addr + 1]

if __name__== "__main__":
  main()
