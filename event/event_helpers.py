import array

from doslib.rom import Rom


def is_addr(addr: int) -> bool:
    return 0x8000000 <= addr <= 0x9000000


# Simple routine to convert a memory address to an index into the ROM.
def addr_to_offset(addr: int) -> int:
    return addr - 0x8000000


def offset_to_addr(offset: int) -> int:
    return offset + 0x8000000


def format_output(cmd: str, addr: int) -> str:
    output = cmd
    while len(output) < 60:
        output += " "
    return f"{output} ; {hex(addr)}"


# Looks up the starting memory address of an event given its ID
def lookup_event(rom: Rom, event_id: int) -> int:
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
    lut_addr = addr_to_offset(((event_id - lut_id_offset) * 4) + lut_base)
    # Since it's stored little endian, we only really need the
    # first two bytes.
    return addr_to_offset(array.array("I", rom.rom_data[lut_addr:lut_addr + 4])[0])
