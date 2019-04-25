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


def _da_rest(cmd: bytearray) -> str:
    cmd_text = "db "
    for cmd_byte in cmd:
        cmd_text += f"{hex(cmd_byte)} "
    return cmd_text.rstrip()


def _da_00(cmd: bytearray) -> str:
    return f"end_event"


def _da_05(cmd: bytearray) -> str:
    dialog_id = array.array("H", cmd[2:4])[0]
    if cmd[4] == 0:
        location = "top"
    else:
        location = "bot"
    return f"load_text {location} {hex(dialog_id)}"


def _da_06(cmd: bytearray) -> str:
    if cmd[3] == 0:
        method = "auto"
    else:
        method = "wait"
    return f"close_dialog {method}"


def _da_0c(cmd: bytearray) -> tuple:
    addr = array.array("I", cmd[4:8])[0]
    return "jump $$addr$$", addr


def _da_11(cmd: bytearray) -> str:
    item_id = array.array("H", cmd[4:6])[0]
    return f"music {hex(cmd[2])} {hex(item_id)}"


def _da_27(cmd: bytearray) -> str:
    return f"show_dialog"


def _da_2d(cmd: bytearray) -> tuple:
    jump_to = None

    if len(cmd) == 4:
        cmd_text = f"set_flag {hex(cmd[2])}"
    else:
        check_flag_cmds = {
            0x2: "jz",
            0x3: "jnz"
        }
        addr = array.array("I", cmd[4:8])[0]
        if cmd[3] in check_flag_cmds:
            cond = check_flag_cmds[cmd[3]]
        else:
            cond = hex(cmd[3])

        cmd_text = f"check {hex(cmd[2])} {cond} $$addr$$"
        jump_to = addr

    return cmd_text, jump_to


def _da_2e(cmd: bytearray) -> str:
    event_id = array.array("H", cmd[2:4])[0]
    return f"remove_trigger {hex(event_id)}"


def _da_30(cmd: bytearray) -> str:
    actions = {
        0x4: "no_collision",
    }
    if cmd[2] in actions:
        action = actions[cmd[2]]
    else:
        action = hex(cmd[2])
    return f"npc_update {action} {hex(cmd[3])}"


def _da_37(cmd: bytearray) -> tuple:
    actions = {
        0x0: "give_item",
        0x1: "take_item",
        0x2: "check_item"
    }

    # We're only handling a subset...
    if cmd[2] not in actions:
        return _da_rest(cmd), None

    jump_to = None

    if len(cmd) == 4:
        cmd_text = f"{actions[cmd[2]]} {hex(cmd[3])}"
    else:
        addr = array.array("I", cmd[4:8])[0]
        cmd_text = f"{actions[cmd[2]]} {hex(cmd[3])} jz $$addr$$"
        jump_to = addr

    return cmd_text, jump_to


def disassemble(rom: Rom, offset: int) -> dict:
    rom_data = rom.rom_data
    working = dict()

    labels = dict()

    if offset < 0 or offset > len(rom_data):
        print(f"Invalid address: {hex(offset)}")
        return working

    last_cmd = -1
    while last_cmd != 0:
        # Name some things (for readability)
        cmd = rom_data[offset]
        cmd_len = rom_data[offset + 1]

        full_cmd = rom_data[offset:offset + cmd_len]

        if cmd == 0x0:
            working[offset] = _da_00(full_cmd)
        elif cmd == 0x5:
            working[offset] = _da_05(full_cmd)
        elif cmd == 0x6:
            working[offset] = _da_06(full_cmd)
        elif cmd == 0xc:
            cmd_text, jump_target = _da_0c(full_cmd)
            if jump_target is not None:
                if jump_target not in labels:
                    labels[jump_target] = f".Label_{len(labels) + 1}"
                label = labels[jump_target]
                cmd_text = cmd_text.replace("$$addr$$", label)
            working[offset] = cmd_text
        elif cmd == 0x11:
            working[offset] = _da_11(full_cmd)
        elif cmd == 0x27:
            working[offset] = _da_27(full_cmd)
        elif cmd == 0x2d:
            cmd_text, jump_target = _da_2d(full_cmd)
            if jump_target is not None:
                if jump_target not in labels:
                    labels[jump_target] = f".Label_{len(labels) + 1}"
                label = labels[jump_target]
                cmd_text = cmd_text.replace("$$addr$$", label)
            working[offset] = cmd_text
        elif cmd == 0x2e:
            working[offset] = _da_2e(full_cmd)
        elif cmd == 0x30:
            working[offset] = _da_30(full_cmd)
        elif cmd == 0x37:
            cmd_text, jump_target = _da_37(full_cmd)
            if jump_target is not None:
                if jump_target not in labels:
                    labels[jump_target] = f".Label_{len(labels) + 1}"
                label = labels[jump_target]
                cmd_text = cmd_text.replace("$$addr$$", label)
            working[offset] = cmd_text
        else:
            working[offset] = _da_rest(full_cmd)

        last_cmd = cmd
        offset = offset + cmd_len

    for offset, cmd in sorted(working.items(), key=lambda x: x[0]):
        addr = offset_to_addr(offset)
        if addr in labels:
            print(format_output(labels[addr], addr))
        print(format_output(cmd, addr))


def disassemble_event(rom: Rom, event_id: int) -> dict:
    # Decompile the event in a function so it can recurse.
    offset = lookup_event(rom, event_id)
    return disassemble(rom, offset)


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
