#!/usr/bin/env python3
import array
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

run_patch = """
; --- Keep this part from the "always dash" patch ---
0x08056480:  02 20    movs r0, #2
0x08056482:  08 40    ands r0, r1
0x08056484:  00 28    cmp  r0, #0
0x08056486:  01 D0    beq  #0x805648c
0x08056488:  01 20    movs r0, #1
0x0805648a:  45 40    eors r5, r0
0x0805648c:  00 2D    cmp  r5, #0
0x0805648e:  0B D0    beq  #0x80564a8

; --- This is the part you will modify ---
; Re-insert the vehicle check here
0x08056490:  52 46    mov  r2, sl          ; <--- NEW
0x08056492:  10 69    ldr  r0, [r2, #0x10] ; <--- NEW
0x08056494:  00 28    cmp  r0, #0          ; <--- NEW
0x08056496:  07 D1    bne  #0x80564a8      ; <--- NEW (Recalculated Branch)

; --- The rest of the NOPs and code remain ---
0x08056498:  00 00    movs r0, r0         ; This NOP is harmless
0x0805649a:  00 00    movs r0, r0         ; This NOP is harmless
0x0805649c:  00 00    movs r0, r0         ; This NOP is harmless
0x0805649e:  14 4B    ldr  r3, [pc, #0x50] ; Dash action continues...
"""


def is_event(rom: Rom, start_offset: int):
    try:
        cmds = 0
        offset = start_offset

        while cmds < 5:
            op = rom.rom_data[offset]
            sz = rom.rom_data[offset + 1]
            if sz % 4 != 0:
                return False

            if op == 0 and sz == 4:
                m = rom.rom_data[offset + 2] == 0xff \
                    and rom.rom_data[offset + 3] == 0xff
                return rom.rom_data[offset + 2] == 0xff and rom.rom_data[offset + 3] == 0xff
            else:
                offset = offset + sz
                if offset > len(rom.rom_data):
                    print(f"Cmd {hex(op)} with size {sz} pushed OOB")
            cmds += 1
    except Exception as e:
        return False

    # All commands passed
    return True


def is_event_lut(rom: Rom, lut: int, count: int):
    try:
        for ent in range(count):
            lut_offset = lut + (ent * 4)
            addr = array.array("I", rom.rom_data[lut_offset:lut_offset + 4])[0]
            offset = rom.pointer_to_offset(addr)
            if not is_event(rom, offset):
                return False
        return True
    except Exception as e:
        print(f"   ! Exception: {e}")
        return False


def find_luts(rom: Rom):
    offset = 0
    rom_size = len(rom.rom_data)
    top_addr = rom.offset_to_pointer(rom_size)

    offset_start = 0
    addr_count = 0

    while offset < rom_size:
        value = array.array("I", rom.rom_data[offset:offset + 4])[0]

        check_ptr = False
        if 0x08000000 < value < top_addr:
            check_ptr = True

        if offset == 0x73a0:
            print(f"offset={hex(offset)}, offset_start={hex(offset_start)}, check_ptr={check_ptr}")

        if check_ptr and is_event(rom, rom.pointer_to_offset(value)):
            if addr_count == 0:
                offset_start = offset
            addr_count += 1
        else:
            if addr_count > 3:
                events = is_event_lut(rom, offset_start, addr_count)

                if events:
                    print(
                        f"Found LUT: {hex(offset_start)} -- {addr_count} entries")

            offset_start = 0
            addr_count = 0
        offset += 4


def main():
    parser = ArgumentParser(
        description="Final Fantasy: Dawn of Souls Event->Script")
    parser.add_argument("rom_path", help="The ROM file to randomize.")
    parsed = parser.parse_args()

    with open(parsed.rom_path, "rb") as rom_file:
        rom_data = bytearray(rom_file.read())
        rom_file.close()
        rom = Rom(rom_data)

    find_luts(rom)


if __name__ == "__main__":
    main()
