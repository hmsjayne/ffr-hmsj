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


def _da_03(cmd: bytearray) -> str:
    map_id = cmd[3]
    x_pos = array.array("H", cmd[4:6])[0]
    y_pos = array.array("H", cmd[6:8])[0]
    x_param = cmd[8]
    y_param = cmd[9]
    return f"load_map {hex(map_id)} {x_pos} {y_pos} {x_param} {y_param}"


def _da_05(cmd: bytearray) -> str:
    dialog_id = array.array("H", cmd[2:4])[0]
    if cmd[4] == 0:
        location = "WINDOW_TOP"
    else:
        location = "WINDOW_BOTTOM"
    return f"load_text {location} {hex(dialog_id)}"


def _da_06(cmd: bytearray) -> str:
    if cmd[3] == 0:
        method = "DIALOG_AUTO_CLOSE"
    else:
        method = "DIALOG_WAIT"
    return f"close_dialog {method}"


def _da_09(cmd: bytearray) -> str:
    frame_count = array.array("H", cmd[2:4])[0]
    return f"delay {frame_count}"


def _da_0b(cmd: bytearray) -> str:
    tiles_to_move = cmd[2]
    speed = cmd[3]
    direction = cmd[4]
    npc_id = cmd[8]
    return f"move_npc {hex(npc_id)} {direction} {tiles_to_move} {speed}"


def _da_0c(cmd: bytearray) -> tuple:
    addr = array.array("I", cmd[4:8])[0]
    return "jump $$addr$$", addr


def _da_0d(cmd: bytearray) -> tuple:
    if len(cmd) == 0x8:
        addr = array.array("I", cmd[4:8])[0]
        return "jump_chest_empty $$addr$$", addr
    else:
        return _da_rest(cmd), None


def _da_11(cmd: bytearray) -> str:
    item_id = array.array("H", cmd[4:6])[0]
    return f"music {hex(cmd[2])} {hex(item_id)}"


def _da_13(cmd: bytearray) -> str:
    sprite_id = cmd[2]
    npc_index = cmd[3]
    x_pos = array.array("H", cmd[8:10])[0]
    y_pos = array.array("H", cmd[10:12])[0]
    return f"add_npc {hex(sprite_id)} {hex(npc_index)} {x_pos} {y_pos}"


def _da_14(cmd: bytearray) -> str:
    npc_id = array.array("H", cmd[2:4])[0]
    return f"remove_npc {hex(npc_id)}"


def _da_19(cmd: bytearray) -> tuple:
    if cmd[1] == 0x4:
        return f"set_repeat {hex(cmd[3])}", None
    else:
        addr = array.array("I", cmd[4:8])[0]
        return f"repeat {hex(cmd[2])} $$addr$$", addr


def _da_1f(cmd: bytearray) -> str:
    return f"set_npc_frame {hex(cmd[2])} {hex(cmd[3])}"


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

        cmd_text = f"check_flag {hex(cmd[2])} {cond} $$addr$$"
        jump_to = addr

    return cmd_text, jump_to


def _da_2e(cmd: bytearray) -> str:
    event_id = array.array("H", cmd[2:4])[0]
    return f"remove_trigger {hex(event_id)}"


def _da_30(cmd: bytearray) -> str:
    action = cmd[2]
    npc_index = cmd[3]

    if len(cmd) == 0x8:
        if action == 0x1:
            event_id = array.array("H", cmd[4:6])[0]
            return f"set_npc_event {hex(npc_index)} {hex(event_id)}"
        else:
            return _da_rest(cmd)

    return f"npc_update {hex(action)} {hex(npc_index)}"


def _da_36(cmd: bytearray) -> str:
    event_id = array.array("H", cmd[2:4])[0]
    return f"remove_all {hex(event_id)}"


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


def _da_42(cmd: bytearray) -> tuple:
    up_addr = array.array("I", cmd[4:8])[0]
    right_addr = array.array("I", cmd[8:12])[0]
    left_addr = array.array("I", cmd[12:16])[0]
    return "jump_by_dir $$up_addr$$ $$right_addr$$ $$left_addr$$", [up_addr, right_addr, left_addr]


def _da_45(cmd: bytearray) -> str:
    npc_id = cmd[2]
    direction = cmd[3]
    x_pos = array.array("H", cmd[4:6])[0]
    y_pos = array.array("H", cmd[6:8])[0]
    return f"move_npc {hex(npc_id)} {direction} {x_pos} {y_pos}"


def _da_48(cmd: bytearray) -> tuple:
    sub_addr = array.array("I", cmd[4:8])[0]
    return "call $$addr$$", sub_addr


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
        elif cmd == 0x3:
            working[offset] = _da_03(full_cmd)
        elif cmd == 0x5:
            working[offset] = _da_05(full_cmd)
        elif cmd == 0x6:
            working[offset] = _da_06(full_cmd)
        elif cmd == 0x9:
            working[offset] = _da_09(full_cmd)
        elif cmd == 0xb:
            working[offset] = _da_0b(full_cmd)
        elif cmd == 0xc:
            cmd_text, jump_target = _da_0c(full_cmd)
            if jump_target is not None:
                if jump_target not in labels:
                    labels[jump_target] = f".Label_{len(labels) + 1}"
                label = labels[jump_target]
                cmd_text = cmd_text.replace("$$addr$$", label)
            working[offset] = cmd_text
        elif cmd == 0xd:
            cmd_text, jump_target = _da_0d(full_cmd)
            if jump_target is not None:
                if jump_target not in labels:
                    labels[jump_target] = f".Label_{len(labels) + 1}"
                label = labels[jump_target]
                cmd_text = cmd_text.replace("$$addr$$", label)
            working[offset] = cmd_text
        elif cmd == 0x11:
            working[offset] = _da_11(full_cmd)
        elif cmd == 0x13:
            working[offset] = _da_13(full_cmd)
        elif cmd == 0x14:
            working[offset] = _da_14(full_cmd)
        elif cmd == 0x19:
            cmd_text, jump_target = _da_19(full_cmd)
            if jump_target is not None:
                if jump_target not in labels:
                    labels[jump_target] = f".Label_{len(labels) + 1}"
                label = labels[jump_target]
                cmd_text = cmd_text.replace("$$addr$$", label)
            working[offset] = cmd_text
        elif cmd == 0x1f:
            working[offset] = _da_1f(full_cmd)
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
        elif cmd == 0x36:
            working[offset] = _da_36(full_cmd)
        elif cmd == 0x37:
            cmd_text, jump_target = _da_37(full_cmd)
            if jump_target is not None:
                if jump_target not in labels:
                    labels[jump_target] = f".Label_{len(labels) + 1}"
                label = labels[jump_target]
                cmd_text = cmd_text.replace("$$addr$$", label)
            working[offset] = cmd_text
        elif cmd == 0x42:
            cmd_text, jump_targets = _da_42(full_cmd)

            addr_labels = ["Up", "Right", "Left"]
            label_num = len(labels) + 1
            token_addr_labels = ["$$up_addr$$", "$$right_addr$$", "$$left_addr$$"]
            for index, jump_target in enumerate(jump_targets):
                if jump_target not in labels:
                    labels[jump_target] = f".Label_{label_num}_{addr_labels[index]}"
                label = labels[jump_target]
                cmd_text = cmd_text.replace(token_addr_labels[index], label)
            working[offset] = cmd_text
        elif cmd == 0x45:
            working[offset] = _da_45(full_cmd)
        elif cmd == 0x48:
            cmd_text, jump_target = _da_48(full_cmd)
            if jump_target is not None:
                if jump_target not in labels:
                    labels[jump_target] = f".Sub_{len(labels) + 1}"
                    print(f"{labels[jump_target]}:")
                    disassemble(rom, addr_to_offset(jump_target))
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
            print(f"{labels[addr]}:")
        print(cmd)


def disassemble_event(rom: Rom, event_id: int) -> dict:
    # Decompile the event in a function so it can recurse.
    offset = lookup_event(rom, event_id)
    return disassemble(rom, offset)
