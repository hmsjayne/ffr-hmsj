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

from doslib.event import EventTextBlock
from doslib.maps import Maps
from doslib.rom import Rom
from event.consts import get_flag_name, sprite_id_to_name, get_map_name, get_key_item_name

# Used for various pieces of data
item_names = {}
event_names = {}
music_names = {}

rom: Rom | None = None
map_index: int = -1

event_text_block: EventTextBlock | None = None

event_to_map_id = {
    0x138b: ["Confronting_Garland", 0x1F],
    0x138d: ["Adamantite_obtaining", 0x5D],
    0x138e: ["Airship_rises_from_Ryukahn_Desert", 0x0],
    0x138f: ["Fairy_gets_Oxyale", 0x47],
    0x1390: ["Confronting_Astos", 0x58],
    0x1391: ["Giving_Crystal_Eye_to_Matoya", 0x61],
    0x1393: ["Nerrick_uses_Nitro_Powder", 0x57],
    0x1394: ["Receive_Canoe", 0x2F],
    0x1395: ["Receive_Chime", 0x70],
    0x1396: ["Class_change", 0x55],
    0x1398: ["Crown_chest", 0x5B],
    0x139a: ["Give_Jolt_Tonic_to_Healer", 0x06],
    0x139c: ["Use_Rod_in_Earth_B3", 0x03],
    0x139d: ["Give_Adamantite_to_Smyth", 0x57],
    0x139f: ["Levistone_obtaining", 0x44],
    0x13a3: ["Confronting_Kraken", 0x17],
    0x13a5: ["Unne_deciphers_Rosetta_Stone", 0x0],
    0x13a7: ["Receive_Lute", 0x39],
    0x13a8: ["Confronting_Marilith", 0x2E],
    0x13aa: ["Rat_Tail_chest", 0x4F],
    0x13ad: ["Nitro_Powder_chest", 0x38],
    0x13b3: ["Confronting_Lich", 0x05],
    0x13b4: ["Rosetta_Stone_chest", 0x1E],
    0x13b5: ["Confronting_Bikke", 0x62],
    0x13b7: ["Star_Ruby_chest", 0x03],
    0x13b8: ["Receive_Earth_Rod", 0x37],
    0x13bb: ["Confronting_Tiamat", 0x60],
    0x13bd: ["Robot_gives_Warp_Cube", 0x53],
    0x1F49: ["Cornelia_fountain", 0x3A],
    0x1f60: ["Chancellor_of_Cornelia", 0x39],
    0xfa6: ["Bridge_Credits", 0x0],
}


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


def get_npc_name(npc_index: int, index_offset: int = 0) -> str:
    if 0x20 <= (npc_index + index_offset) <= 0x23:
        # Special case for the PC(s)
        return f"%PC_{hex(npc_index)}"

    if 0 <= map_index < 0xd3:
        maps = Maps(rom)
        map = maps.get_map(map_index)
        npcs = map.npcs
        if npc_index < len(npcs):
            npc = npcs[npc_index].sprite_id
            if npc in sprite_id_to_name:
                return f"%NPC_{sprite_id_to_name[npc]}_{hex(npc_index)}"
    return hex(npc_index)


# Looks up the starting memory address of an event given its ID
def lookup_event(rom: Rom, event_id: int) -> int | None:
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
        return None

    # This is the address of the pointer in the LUT
    lut_addr = addr_to_offset(((event_id - lut_id_offset) * 4) + lut_base)
    # Since it's stored little endian, we only really need the
    # first two bytes.
    addr = addr_to_offset(array.array("I", rom.rom_data[lut_addr:lut_addr + 4])[0])
    if addr < 0:
        raise ValueError("Event id invalid: " + hex(event_id))
    return addr


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
    map_name = get_map_name(map_id)

    global map_index
    map_index = map_id
    return f"load_map {map_name} {x_pos} {y_pos} {x_param} {y_param}"


def _da_05(cmd: bytearray) -> str:
    dialog_id = array.array("H", cmd[2:4])[0]
    if cmd[4] == 0:
        location = "WINDOW_TOP"
    else:
        location = "WINDOW_BOTTOM"

    text = event_text_block[dialog_id].replace("\n", "\\n")
    return f"load_text {location} {hex(dialog_id)} ; \"{text}\\x00\""


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
    npc_name = get_npc_name(npc_id)
    return f"move_npc {npc_name} {direction} {tiles_to_move} {speed}"


def _da_0c(cmd: bytearray) -> tuple:
    addr = array.array("I", cmd[4:8])[0]
    return "goto $$addr$$", addr


def _da_0d(cmd: bytearray) -> tuple:
    if len(cmd) == 0x8:
        addr = array.array("I", cmd[4:8])[0]
        return "jump_chest_empty $$addr$$", addr
    else:
        return _da_rest(cmd), None


def _da_11(cmd: bytearray) -> str:
    item_id = array.array("H", cmd[4:6])[0]
    music_name = music_names[item_id] if item_id in music_names else hex(item_id)
    return f"music {hex(cmd[2])} {music_name}"


def _da_13(cmd: bytearray) -> str:
    if len(cmd) < 12:
        return _da_rest(cmd)
    sprite_id = cmd[2]
    npc_index = cmd[3]
    x_pos = array.array("H", cmd[8:10])[0]
    y_pos = array.array("H", cmd[10:12])[0]
    return f"add_npc {hex(sprite_id)} {hex(npc_index)} {x_pos} {y_pos}"


def _da_14(cmd: bytearray) -> str:
    npc_id = cmd[2]
    mode = cmd[3]

    index_offset = 0x20 if mode == 0x1 else 0
    npc_name = get_npc_name(npc_id, index_offset)
    return f"remove_npc {npc_name} {hex(mode)}"


def _da_19(cmd: bytearray) -> tuple:
    if cmd[1] == 0x4:
        return f"set_repeat {hex(cmd[3])}", None
    else:
        addr = array.array("I", cmd[4:8])[0]
        return f"repeat {hex(cmd[2])} $$addr$$", addr


def _da_1f(cmd: bytearray) -> str:
    npc_name = get_npc_name(cmd[2])
    return f"set_npc_frame {npc_name} {hex(cmd[3])}"


def _da_27(cmd: bytearray) -> str:
    return f"show_dialog"


def _da_2d(cmd: bytearray) -> tuple:
    jump_to = None

    if len(cmd) == 4:
        flag_name = get_flag_name(cmd[2])
        cmd_text = f"set_flag {flag_name}"
        label_name = None
    else:
        check_flag_cmds = {
            0x2: "unset",
            0x3: "set"
        }
        addr = array.array("I", cmd[4:8])[0]
        if cmd[3] in check_flag_cmds:
            cond = check_flag_cmds[cmd[3]]
        else:
            cond = hex(cmd[3])

        flag_name = get_flag_name(cmd[2])
        cmd_text = f"if {flag_name} {cond} goto $$addr$$"
        jump_to = addr
        if flag_name.startswith("%"):
            label_name = f"{flag_name[1:]}_{cond[0].upper()}{cond[1:]}"
        else:
            label_name = f"{hex(cmd[2])}_{cond[0].upper()}{cond[1:]}"

    return cmd_text, jump_to, label_name


def _da_2e(cmd: bytearray) -> str:
    event_id = array.array("H", cmd[2:4])[0]
    event_name = event_names[event_id] if event_id in event_names else hex(event_id)
    return f"remove_trigger {event_name}"


def _da_2f(cmd: bytearray) -> tuple:
    something = array.array("H", cmd[2:4])[0]
    addr = array.array("I", cmd[4:8])[0]
    return f"goto_far {hex(something)} $$addr$$", addr


def _da_30(cmd: bytearray) -> str:
    action = cmd[2]
    npc_index = cmd[3]

    if len(cmd) == 0x8:
        if action == 0x1:
            event_id = array.array("H", cmd[4:6])[0]
            npc_name = get_npc_name(npc_index)
            return f"set_npc_event {npc_name} {hex(event_id)}"
        else:
            return _da_rest(cmd)

    npc_name = get_npc_name(npc_index)
    return f"npc_update {hex(action)} {npc_name}"


def _da_36(cmd: bytearray) -> str:
    event_id = array.array("H", cmd[2:4])[0]
    event_name = event_names[event_id] if event_id in event_names else hex(event_id)
    return f"remove_all {event_name}"


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

    item_name = get_key_item_name(cmd[3])
    if len(cmd) == 4:
        cmd_text = f"{actions[cmd[2]]} {item_name}"
    else:
        addr = array.array("I", cmd[4:8])[0]
        cmd_text = f"{actions[cmd[2]]} {item_name} jz $$addr$$"
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
    npc_name = get_npc_name(npc_id)
    return f"move_npc {npc_name} {direction} {x_pos} {y_pos}"


def _da_48(cmd: bytearray) -> tuple:
    sub_addr = array.array("I", cmd[4:8])[0]
    return "call $$addr$$", sub_addr


def disassemble(rom: Rom, offset: int) -> (dict[int, str], dict[int, str]):
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
            cmd_text, jump_target, label_name = _da_2d(full_cmd)
            if jump_target is not None:
                if jump_target not in labels:
                    labels[jump_target] = f".Label_{len(labels) + 1}_{label_name}"
                label = labels[jump_target]
                cmd_text = cmd_text.replace("$$addr$$", label)
            working[offset] = cmd_text
        elif cmd == 0x2e:
            working[offset] = _da_2e(full_cmd)
        elif cmd == 0x2f and False:  # Update if this is understood at some point
            cmd_text, jump_target = _da_2f(full_cmd)
            if jump_target is not None:
                if jump_target not in labels:
                    labels[jump_target] = f".Label_{len(labels) + 1}"
                label = labels[jump_target]
                cmd_text = cmd_text.replace("$$addr$$", label)
            working[offset] = cmd_text
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

    return working, labels


def disassemble_event(workingRom: Rom, event_id: int = None, addr: int = None) -> (dict[int, str], dict[int, str]):
    global event_text_block
    global event_names
    global music_names
    global rom
    global map_index

    rom = workingRom

    if event_text_block is None:
        event_text_block = EventTextBlock(rom)
    if len(event_names.keys()) == 0:
        with open("scripts/DosLib.script", "r") as std_inc:
            for line in std_inc.readlines():
                if line.startswith(";"):
                    continue
                if line.startswith("%"):
                    parts = line.split(" ")
                    name = parts[0]
                    value = int(parts[1], 16)
                    if name.find("Event") > 0:
                        event_names[value] = name
                    elif name.find("Item") > 0:
                        item_names[value] = name
                    elif name.find("Music") > 0:
                        music_names[value] = name

    # Decompile the event in a function so it can recurse.
    if addr is not None:
        offset = addr
    else:
        if 0 <= event_id <= 0xd3:
            map_index = event_id
        elif event_id in event_to_map_id:
            map_index = event_to_map_id[event_id][1]
        else:
            map_index = -1
        offset = lookup_event(rom, event_id)
    return disassemble(rom, offset)
