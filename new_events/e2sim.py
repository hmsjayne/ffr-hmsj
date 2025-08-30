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

import struct
import typing
from collections import namedtuple

from doslib.rom import Rom
from event.event_helpers import addr_to_offset, is_addr, lookup_event, offset_to_addr
from new_events.ctrl_flow import *


def fallback(ins: bytearray) -> tuple[tuple, None]:
    unpacked = struct.unpack("B"*ins[1], ins)
    return unpacked, None


def branch(ins: bytearray) -> tuple[tuple, list[int]]:
    unpacked = struct.unpack("<BBxxI", ins)
    branch_ins = Branch(*unpacked)
    return branch_ins, [branch_ins.addr]


def branch_flag(ins: bytearray) -> tuple[tuple, list[int]]:
    unpacked = struct.unpack("<BBBBI", ins)
    branch_ins = BranchOnFlag(*unpacked)
    return branch_ins, [branch_ins.addr]


def branch_by_dir(ins: bytearray) -> tuple[tuple, list[int]]:
    unpacked = struct.unpack("<BBxxIII", ins)
    branch_ins = BranchByDir(*unpacked)
    return branch_ins, [branch_ins.addr_up, branch_ins.addr_right, branch_ins.addr_left]


def call(ins: bytearray) -> tuple[tuple, list[int]]:
    unpacked = struct.unpack("<BBxxI", ins)
    call_ins = Call(*unpacked)
    return call_ins, [call_ins.addr]


def flag_handler(ins: bytearray) -> tuple[tuple, typing.Optional[list[int]]]:
    if ins[1] == 8:
        return branch_flag(ins)
    else:
        return fallback(ins)


instruction_handlers = {
    0xc: branch,
    0x2d: flag_handler,
    0x42: branch_by_dir,
    0x48: call
}


def disassemble(rom: Rom, offset: int) -> typing.Optional[dict[int, tuple]]:
    rom_data = rom.rom_data

    if offset < 0 or offset > len(rom_data):
        print(f"Invalid address: {hex(offset)}")
        return None

    program: dict[int, tuple] = dict()
    next_addrs = [offset]

    while next_addrs:
        addr = next_addrs.pop()

        if not is_addr(addr):
            addr = offset_to_addr(addr)

        # If we already decompiled this instruction, skip it
        if addr in program:
            continue

        # Reading from the rom is by offset
        offset = addr_to_offset(addr)

        # Name some things (for readability)
        opcode = rom_data[offset]
        ins_size = rom_data[offset + 1]

        full_ins = rom_data[offset:offset + ins_size]

        if opcode in instruction_handlers:
            decoded, addrs = instruction_handlers[opcode](full_ins)
            if addrs is not None:
                for addr in addrs:
                    next_addrs.append(addr)
        else:
            decoded, _ = fallback(full_ins)

        # Add the decoded instruction to the program
        program[offset_to_addr(offset)] = decoded

        if opcode != 0:
            offset = offset + ins_size
            next_addrs.append(offset)

    return program


def disassemble_event(rom: Rom, event_id: int):
    # Decompile the event in a function so it can recurse.
    offset = lookup_event(rom, event_id)

    program = disassemble(rom, offset)
    if program is not None:
        cfg = build_cfg(program)
        blocks = detect_if_then_else(cfg)
        for ifelse in blocks:
            print(f"- {ifelse}")
