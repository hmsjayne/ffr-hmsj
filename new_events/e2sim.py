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
from event.event_helpers import (addr_to_offset, is_addr, lookup_event,
                                 offset_to_addr)
from new_events.ctrl_flow import *
from new_events.instructions import *
from new_events.ast_gen import build_ast_from_analysis, print_ast
from new_events.script_gen import generate_script_from_ast


def fallback(ins: bytearray) -> tuple[GenericInstruction, None]:
    opcode = ins[0]
    size = ins[1]
    params_bytes = bytes(ins[2:size])
    fallback_ins = GenericInstruction(opcode, size, params_bytes)
    return fallback_ins, None


def ret_instruction(ins: bytearray) -> tuple[ReturnInstruction, None]:
    opcode = ins[0]
    size = ins[1]
    params_bytes = bytes(ins[2:size])
    return_ins = ReturnInstruction(opcode, size, params_bytes)
    return return_ins, None


def branch(ins: bytearray) -> tuple[Branch, list[int]]:
    unpacked = struct.unpack("<BBxxI", ins)
    branch_ins = Branch(*unpacked)
    return branch_ins, [branch_ins.addr]


def branch_flag(ins: bytearray) -> tuple[BranchOnFlag, list[int]]:
    unpacked = struct.unpack("<BBBBI", ins)
    branch_ins = BranchOnFlag(*unpacked)
    return branch_ins, [branch_ins.addr]


def branch_by_dir(ins: bytearray) -> tuple[BranchByDir, list[int]]:
    unpacked = struct.unpack("<BBxxIII", ins)
    branch_ins = BranchByDir(*unpacked)
    return branch_ins, [branch_ins.addr_up, branch_ins.addr_right, branch_ins.addr_left]


def call(ins: bytearray) -> tuple[Call, list[int]]:
    unpacked = struct.unpack("<BBxxI", ins)
    call_ins = Call(*unpacked)
    return call_ins, [call_ins.addr]


def loop_handler(ins: bytearray) -> tuple[BaseInstruction, typing.Optional[list[int]]]:
    if ins[1] == 8:
        # LoopEnd: step is in byte 2 (0x1), byte 3 is always 0xff
        unpacked = struct.unpack("<BBBxI", ins)
        loop_ins = LoopEnd(*unpacked)
        return loop_ins, [loop_ins.addr]
    else:
        # LoopStart: count is unsigned byte, not signed 16-bit
        unpacked = struct.unpack("<BBxB", ins)
        loop_ins = LoopStart(*unpacked)
        return loop_ins, None


def gil_handler(ins: bytearray) -> tuple[BaseInstruction, typing.Optional[list[int]]]:
    if ins[1] == 8:
        unpacked = struct.unpack("<BBxxI", ins)
        branch_ins = BranchOnGil(*unpacked)
        return branch_ins, [branch_ins.addr]
    else:
        return fallback(ins)


def flag_handler(ins: bytearray) -> tuple[BaseInstruction, typing.Optional[list[int]]]:
    if ins[1] == 8:
        return branch_flag(ins)
    else:
        return fallback(ins)


def item_handler(ins: bytearray) -> tuple[BaseInstruction, typing.Optional[list[int]]]:
    if ins[1] == 8:
        unpacked = struct.unpack("<BBBBI", ins)
        branch_ins = BranchOnItem(*unpacked)
        return branch_ins, [branch_ins.addr]
    else:
        return fallback(ins)


def yesno_handler(ins: bytearray) -> tuple[BaseInstruction, typing.Optional[list[int]]]:
    """Handle Yes/No dialog instruction (0x63)."""
    if ins[1] == 8:
        unpacked = struct.unpack("<BBxxI", ins)
        branch_ins = BranchOnYesNo(*unpacked)
        return branch_ins, [branch_ins.addr]
    else:
        return fallback(ins)


instruction_handlers = {
    0x0: ret_instruction,
    0xc: branch,
    0x19: loop_handler,
    0x2a: gil_handler,
    0x2d: flag_handler,
    0x37: item_handler,
    0x42: branch_by_dir,
    0x48: call,
    0x63: yesno_handler
}


def disassemble(rom: Rom, offset: int) -> typing.Optional[dict[int, BaseInstruction]]:
    rom_data = rom.rom_data

    if offset < 0 or offset > len(rom_data):
        print(f"Invalid address: {hex(offset)}")
        return None

    program: dict[int, BaseInstruction] = dict()
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
            next_offset = offset + ins_size
            next_addrs.append(offset_to_addr(next_offset))

    return program


def disassemble_event(rom: Rom, event_id: int):
    # Decompile the event in a function so it can recurse.
    offset = lookup_event(rom, event_id)

    program = disassemble(rom, offset)
    if program is not None:
        cfg = build_cfg(program)

        # Comprehensive analysis with annotations
        analysis = analyze_control_flow(cfg)

        print(f":: Control Flow Analysis ::")
        print(f"Entry Point: {hex(analysis['entry_point']) if analysis['entry_point'] else 'None'}")
        print(f"Total Blocks: {analysis['total_blocks']}")
        print(f"Complexity Metrics: {analysis['complexity_metrics']}")
        print()

        print(f":: Loops ::")
        for loop_info in analysis['patterns']['loops']:
            print(f"- Type: {loop_info.get('type', 'unknown')}")
            print(f"  Init blocks: {[hex(x) for x in loop_info.get('loop_init', [])]}")
            print(f"  Header: {hex(loop_info.get('loop_header', 0))}")
            print(f"  Body blocks: {[hex(x) for x in loop_info.get('loop_body_blocks', [])]}")
            print(f"  Is nested: {loop_info.get('is_nested', False)}")
            print()

        print(f":: Conditionals ::")
        for cond_info in analysis['patterns']['conditionals']:
            print(f"- Pattern: {cond_info.get('pattern_type', 'unknown')}")
            print(f"  If block: {hex(cond_info.get('if_block', 0))}")
            print(f"  Then block: {hex(cond_info.get('then_block', 0))}")
            print(f"  Else block: {hex(cond_info.get('else_block', 0))}")
            if 'join_block' in cond_info:
                print(f"  Join block: {hex(cond_info['join_block'])}")
            if 'condition' in cond_info:
                condition = cond_info['condition']
                branch_type = condition['branch_type']
                if branch_type == 'flag':
                    flag_id = condition['flag_id']
                    cond_type = condition['condition_type']
                    print(f"  Condition: flag {flag_id}, type {cond_type}")
                elif branch_type == 'item':
                    item_id = condition['item_index']
                    mode = condition['mode']
                    print(f"  Condition: item {item_id}, mode {mode}")
                elif branch_type == 'gil':
                    print(f"  Condition: gil check")
                elif branch_type == 'yesno':
                    print(f"  Condition: yes/no dialog")
                else:
                    print(f"  Condition: {branch_type}")
            print()

        print(f":: Switches ::")
        for switch_info in analysis['patterns']['switches']:
            print(f"- Pattern: {switch_info.get('pattern_type', 'unknown')}")
            print(f"  Switch block: {hex(switch_info.get('switch_block', 0))}")
            print(f"  Cases: Up={hex(switch_info.get('case_up', 0))}, Right={hex(switch_info.get('case_right', 0))}, Left={hex(switch_info.get('case_left', 0))}, Down={hex(switch_info.get('case_down', 0))}")
            print(f"  Join block: {hex(switch_info.get('join_block', 0))}")
            print(f"  Unique cases: {switch_info.get('unique_cases', 0)}/{switch_info.get('total_cases', 4)}")
            print()

        print(f":: Return Blocks ::")
        for ret_info in analysis['patterns']['returns']:
            print(f"- Block: {hex(ret_info.get('return_block', 0))}")
            print(f"  Predecessors: {[hex(x) for x in ret_info.get('predecessors', [])]}")
            print(f"  Instructions: {ret_info.get('instruction_count', 0)}")
            print()

        print(f":: Block Annotations ::")
        for addr, block_info in analysis['block_types'].items():
            if len(block_info['types']) > 1:  # Only show blocks with interesting annotations
                print(f"- {hex(addr)}: {block_info['types']} ({block_info['instruction_count']} instructions)")

        print()
        print(f":: AST Generation ::")
        try:
            ast = build_ast_from_analysis(cfg, analysis)
            print("AST successfully generated:")
            print_ast(ast)

            print()
            print(f":: Script Code Generation ::")
            script_code = generate_script_from_ast(ast)
            print("Generated script code:")
            print(script_code)
        except Exception as e:
            print(f"AST/Script generation failed: {e}")
            import traceback
            traceback.print_exc()
