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

# This script is used to perform various analysis of events in Final Fantasy 1: Dawn of Souls for the GBA. :)

import array
import sys

from doslib.rom import Rom


# Simple routine to convert a memory address to an index into the ROM.
def addr_to_rom(addr):
    return addr - 0x8000000


# Looks up the starting memory address of an event given its ID
def lookup_event(rom: Rom, event_id: int):
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
    lut_addr = addr_to_rom(((event_id - lut_id_offset) * 4) + lut_base)
    # Since it's stored little endian, we only really need the
    # first two bytes.
    return addr_to_rom(array.array("I", rom.rom_data[lut_addr:lut_addr + 4])[0])


def get_jump_addrs(cmd: bytearray):
    addrs = []
    for base in range(1, int(len(cmd) / 4)):
        index = (base * 4)
        paddr = array.array("I", cmd[index:index + 4])[0]
        if 0x8000000 < paddr <= 0x9000000:
            addrs.append(paddr)
    return addrs


def disassemble(rom: Rom, addr: int) -> dict:
    rom_data = rom.rom_data
    working = dict()

    if addr < 0 or addr > len(rom_data):
        print(f"Invalid address: {hex(addr)}")
        return working

    last_cmd = -1
    while last_cmd != 0:
        # Name some things (for readability)
        cmd = rom_data[addr]
        cmd_len = rom_data[addr + 1]

        full_cmd = rom_data[addr:addr + cmd_len]
        working[addr] = full_cmd

        last_cmd = cmd
        addr = addr + cmd_len

    return working


def decompile(rom: Rom, addr: int) -> dict:
    rom_data = rom.rom_data
    working = dict()

    if addr < 0 or addr > len(rom_data):
        print(f"Invalid address: {hex(addr)}")
        return working

    last_cmd = -1
    while last_cmd != 0:
        # Name some things (for readability)
        cmd = rom_data[addr]
        cmd_len = rom_data[addr + 1]

        full_cmd = rom_data[addr:addr + cmd_len]
        if cmd not in working:
            working[cmd] = []
        working[cmd].append(full_cmd)

        last_cmd = cmd
        addr = addr + cmd_len

    return working


def decompile_event(rom: Rom, event_id: int) -> dict:
    # Decompile the event in a function so it can recurse.
    addr = lookup_event(rom, event_id)
    return decompile(rom, addr)


def get_unique_cmds(rom: Rom, event_ranges) -> tuple:
    event_code = {}
    cmd_counts = {}

    for event_range in event_ranges:
        for event_id in range(event_range[0], event_range[1]):
            new_event_code = decompile_event(rom, event_id)

            for key, value in sorted(new_event_code.items(), key=lambda x: x[0]):
                if key not in event_code:
                    event_code[key] = []
                    cmd_counts[key] = 0

                cmd_counts[key] += len(value)
                for cmd in new_event_code[key]:
                    if cmd not in event_code[key]:
                        event_code[key].append(cmd)

    return event_code, cmd_counts


def print_unique_cmds(rom: Rom, event_ranges):
    event_code, cmd_counts = get_unique_cmds(rom, event_ranges)
    for key, value in sorted(event_code.items(), key=lambda x: x[0]):
        print(f"Command: {hex(key)} ({cmd_counts[key]})")
        for cmd_use in event_code[key]:
            cmd_text = ""
            for cmd in cmd_use:
                cmd_text += f"{hex(cmd)} "
            print(f"  Use: {cmd_text}")


def find_jump_cmds(rom: Rom, event_ranges):
    event_code, cmd_counts = get_unique_cmds(rom, event_ranges)

    jump_cmds = {}
    for key, value in sorted(event_code.items(), key=lambda x: x[0]):
        for cmd in value:
            if len(cmd) == 0x4:
                # Addresses are 4 bytes, so the command has to be at least 8
                continue

            for base in range(1, int(len(cmd) / 4)):
                index = base * 4
                paddr = array.array("I", cmd[index:index + 4])[0]

                if 0x8000000 < paddr <= 0x9000000:
                    if cmd[0] not in jump_cmds:
                        jump_cmds[cmd[0]] = []
                    jump_cmds[cmd[0]].append(cmd)
                    break

    for key, value in sorted(jump_cmds.items(), key=lambda x: x[0]):
        print(f"Command: {hex(key)}")
        for cmd_use in value:
            cmd_text = ""
            for cmd in cmd_use:
                cmd_text += f"{hex(cmd)} "
            print(f"  Use: {cmd_text}")


def find_jumps_out(rom: Rom, event_ranges):
    jump_commands = (0xc, 0x11, 0x13, 0x19, 0x23, 0x2d, 0x30, 0x37, 0x42, 0x4e, 0x83, 0x8b)

    for event_range in event_ranges:
        for event_id in range(event_range[0], event_range[1]):

            jump_targets = []
            event_end = -1

            event_addr = lookup_event(rom, event_id)
            if event_addr < 0:
                continue
            event_start = 0x8000000 + event_addr

            event_code = disassemble(rom, event_addr)
            for addr, cmd in sorted(event_code.items(), key=lambda x: x[0]):
                if addr > event_end:
                    event_end = addr + len(cmd)

                op_code = cmd[0]
                if op_code in jump_commands:
                    jump_targets.extend(get_jump_addrs(cmd))

            event_end += 0x8000000

            wrote_event_id = False
            if len(jump_targets) > 0:
                for target in jump_targets:
                    if target < event_start or target > event_end:
                        if not wrote_event_id:
                            print(f"Event {hex(event_id)}: {hex(event_start)} - {hex(event_end)}")
                            wrote_event_id = True

                        print(f" - Exits event: {hex(target)}")


def main(argv):
    if len(argv) != 1:
        raise ValueError("Please pass ROM path and event ID parameters")

    rom = Rom(argv[0])
    event_ranges = [(0x0, 0xD4), (0xFA0, 0xFAB), (0x1388, 0x13CD), (0x1F40, 0x2030), (0x2328, 0x2405)]

    find_jump_cmds(rom, event_ranges)


if __name__ == "__main__":
    main(sys.argv[1:])
