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

from doslib.rom import Rom
from doslib.textblock import TextBlock

# Globals, because I'm lazy.
rom: Rom
event_text: TextBlock

DIRECTIONS = ["Down", "Up", "Right", "Left"]
SPEEDS = ["Walk", "Run", "Sprint", "Crawl"]


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
    return addr_to_rom(array.array("I", rom.rom_data[lut_addr:lut_addr + 4])[0])


def decompile(addr):
    rom_data = rom.rom_data
    working = dict()
    jumps = []

    if addr < 0 or addr > len(rom_data):
        print(f"Invalid address: {hex(addr)}")
        return working

    last_cmd = -1
    while last_cmd != 0:
        # Name some things (for readability)
        cmd = rom_data[addr]
        cmd_len = rom_data[addr + 1]

        cmd_str = ""
        for i in range(cmd_len):
            cmd_str = cmd_str + hex(rom_data[addr + i]) + " "

        # Check to see if it's a branch, if it is we may want to
        # decompile it as well.
        if cmd == 0x0:
            cmd_str = f"end_event :: {cmd_str}"
        elif cmd == 0x1:
            cmd_str = f"nop :: {cmd_str}"
        elif cmd == 0x5:
            event_string_id = array.array("H", rom_data[addr + 2:addr + 4])[0]
            cmd_str = f"load_text {hex(event_string_id)} :: {cmd_str}\n{event_text[event_string_id]}"
        elif cmd == 0x6:
            if rom_data[addr + 3] == 0:
                cmd_str = f"close_dialog :: {cmd_str}"
            else:
                cmd_str = f"close_dialog, wait :: {cmd_str}"
        elif cmd == 0x9:
            time_to_wait = array.array("H", rom_data[addr + 4:addr + 6])[0]
            cmd_str = f"wait_frames {time_to_wait} :: {cmd_str}"
        elif cmd == 0x0c:
            # Jump command
            jump_target = addr_to_rom(array.array("I", rom_data[addr + 4:addr + 8])[0])
            jumps.append(jump_target)
            cmd_str = f"jump {hex(jump_target)} :: {cmd_str}"
        elif cmd == 0x0d and cmd_len == 0xc:
            first_target = addr_to_rom(array.array("I", rom_data[addr + 4:addr + 8])[0])
            second_target = addr_to_rom(array.array("I", rom_data[addr + 8:addr + 12])[0])
            jumps.append(first_target)
            jumps.append(second_target)
            cmd_str = f"jump?({hex(rom_data[addr + 2])}) {hex(first_target)}, {hex(second_target)} :: {cmd_str}"
        elif cmd == 0x11:
            sub_cmd = rom_data[addr + 2]
            if sub_cmd == 0x0:
                sound_id = array.array("H", rom_data[addr + 4:addr + 6])[0]
                cmd_str = f"play_sound {hex(sound_id)} :: {cmd_str}"
            elif sub_cmd == 0x1:
                music_id = array.array("H", rom_data[addr + 4:addr + 6])[0]
                cmd_str = f"play_music {hex(music_id)} :: {cmd_str}"
            elif sub_cmd == 0x4:
                cmd_str = f"resume_music :: {cmd_str}"
            elif sub_cmd == 0x5 or sub_cmd == 0x6:
                cmd_str = f"fade_music :: {cmd_str}"
            elif sub_cmd == 0x9:
                cmd_str = f"wait_for_sound_effect :: {cmd_str}"
            elif sub_cmd == 0xa:
                cmd_str = f"wait_for_music :: {cmd_str}"
            else:
                cmd_str = cmd_str
        elif cmd == 0x12:
            sprite_id = rom_data[addr + 2]
            coord_mode = rom_data[addr + 3]
            if coord_mode == 0x0:
                sprite_x = array.array("H", rom_data[addr + 6:addr + 8])[0]
                sprite_y = array.array("H", rom_data[addr + 8:addr + 10])[0]
            elif coord_mode == 0x1:
                sprite_x = -1
                sprite_y = -1
            else:
                sprite_x = 0
                sprite_y = 0
            cmd_str = f"load_sprite {hex(sprite_id)}, ({sprite_x}, {sprite_y}) :: {cmd_str}"
        elif cmd == 0x14:
            if rom_data[addr + 3] == 0x1:
                sprite_id = rom_data[addr + 2] + 0x20
            else:
                sprite_id = rom_data[addr + 2]
            cmd_str = f"remove_sprite {sprite_id} :: {cmd_str}"
        elif cmd == 0x15:
            tiles = rom_data[addr + 2]
            speed_index = rom_data[addr + 3]
            speed = SPEEDS[speed_index] if speed_index in SPEEDS else hex(speed_index)
            pc_dirs = [
                DIRECTIONS[rom_data[addr + 4]],
                DIRECTIONS[rom_data[addr + 5]],
                DIRECTIONS[rom_data[addr + 6]],
                DIRECTIONS[rom_data[addr + 7]],
            ]
            cmd_str = f"move_party {speed}, {tiles}, {pc_dirs} :: {cmd_str}"
        elif cmd == 0x16:
            if rom_data[addr + 2] == 0x0:
                cmd_str = f"hide_leader :: {cmd_str}"
            else:
                cmd_str = f"show_leader :: {cmd_str}"
        elif cmd == 0x1f:
            sprite_id = rom_data[addr + 2]
            frame = rom_data[addr + 3]
            cmd_str = f"set_animation_frame {hex(sprite_id)}, frame={frame} :: {cmd_str}"
        elif cmd == 0x26:
            cmd_str = f"face_party {DIRECTIONS[rom_data[addr + 2]]} :: {cmd_str}"
        elif cmd == 0x27:
            cmd_str = f"show_dialog :: {cmd_str}"
        elif cmd == 0x2d and cmd_len == 0x8:
            # 0x2d variant with alternate
            jump_target = addr_to_rom(array.array("I", rom_data[addr + 4:addr + 8])[0])
            jumps.append(jump_target)
            cmd_str = f"check_set_flag_and_jump {hex(rom_data[addr + 2])}, condition={hex(rom_data[addr + 3])}, " \
                f"{hex(jump_target)} :: {cmd_str}"
        elif cmd == 0x2d:
            cmd_str = f"check_set_flag {hex(rom_data[addr + 2])}, condition={hex(rom_data[addr + 3])} :: {cmd_str}"
        elif cmd == 0x2e:
            event_id = array.array("H", rom_data[addr + 2:addr + 4])[0]
            cmd_str = f"remove_trigger {hex(event_id)} :: {cmd_str}"
        elif cmd == 0x37:
            sub_cmd = rom_data[addr + 2]
            item_index = rom_data[addr + 3]
            if sub_cmd == 0x0:
                cmd_str = f"give_item {hex(item_index)} :: {cmd_str}"
            elif sub_cmd == 0x1:
                cmd_str = f"remove_item {hex(item_index)} :: {cmd_str}"
            elif sub_cmd == 0x2:
                jump_target = addr_to_rom(array.array("I", rom_data[addr + 4:addr + 8])[0])
                jumps.append(jump_target)
                cmd_str = f"jump_if_no_item {hex(item_index)}, {hex(jump_target)} :: {cmd_str}"
        elif cmd == 0x3b:
            cmd_str = f"wait_for_party_movement :: {cmd_str}"
        elif cmd == 0x42:
            up_jump = addr_to_rom(array.array("I", rom_data[addr + 4:addr + 8])[0])
            right_jump = addr_to_rom(array.array("I", rom_data[addr + 8:addr + 12])[0])
            left_jump = addr_to_rom(array.array("I", rom_data[addr + 12:addr + 16])[0])
            jumps.append(up_jump)
            jumps.append(right_jump)
            jumps.append(left_jump)
            cmd_str = f"jump_by_dir up={hex(up_jump)}, right={hex(right_jump)}, left={hex(left_jump)} :: {cmd_str}"
        elif cmd == 0x48:
            # Another jump command
            jump_target = addr_to_rom(array.array("I", rom_data[addr + 4:addr + 8])[0])
            jumps.append(jump_target)

        working[addr] = cmd_str

        last_cmd = rom_data[addr]
        addr = addr + rom_data[addr + 1]

    for jump in jumps:
        if jump not in working:
            working.update(decompile(jump))

    return working


def main(argv):
    if len(argv) != 2:
        raise ValueError("Please pass ROM path and event ID parameters")

    global rom, event_text
    rom = Rom(argv[0])
    event_text = TextBlock(rom, 0x211770, 1000)

    if argv[1] == "--strings":
        for idx, estr in enumerate(event_text):
            print(f"({idx}): {estr}")
    else:
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
