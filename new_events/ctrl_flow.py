from collections import OrderedDict
from typing import Optional
from new_events import instructions
from new_events.instructions import *


class BasicBlock:
    def __init__(self, start_address: int):
        self.start_address: int = start_address
        self.instructions: list[BaseInstruction] = []
        self.next_blocks: list[int] = []
        self.predecessors: list[int] = []
        self.type: str = "basic"


class ControlFlowGraph:
    def __init__(self):
        self.blocks: dict[int, BasicBlock] = OrderedDict()
        self.entry_point: Optional[int] = None


def build_cfg(program: dict[int, BaseInstruction]) -> ControlFlowGraph:
    cfg = ControlFlowGraph()
    addresses = sorted(program.keys())

    # Identify block leaders (start of basic blocks)
    leaders = set()
    leaders.add(addresses[0])  # Program entry point

    for addr, code in program.items():
        # Jump instructions create new leaders at their targets
        if isinstance(code, BaseBranch):
            for jump_target in code.branch_addrs():
                leaders.add(jump_target)

                # Instructions after jumps are also leaders
                next_addr = addr + code.size
                if next_addr in program:
                    leaders.add(next_addr)

    # Create basic blocks
    leaders = sorted(leaders)
    for i, leader in enumerate(leaders):
        block = BasicBlock(leader)
        end_addr = leaders[i+1] if i+1 < len(leaders) else max(addresses) + 1

        # Add instructions to block
        current_addr = leader
        while current_addr < end_addr and current_addr in program:
            block.instructions.append(program[current_addr])
            current_addr += program[current_addr].size

        cfg.blocks[leader] = block

    # Connect blocks
    for leader, block in cfg.blocks.items():
        last_instruction = block.instructions[-1]
        last_ins = last_instruction

        if type(last_ins) == BranchOnFlag:
            jump_target = last_ins.branch_addrs()[0]
            next_addr = leader + sum(inst.size for inst in block.instructions)

            if jump_target in cfg.blocks:
                block.next_blocks.append(jump_target)
                cfg.blocks[jump_target].predecessors.append(leader)

            if next_addr in cfg.blocks:
                block.next_blocks.append(next_addr)
                cfg.blocks[next_addr].predecessors.append(leader)

        elif type(last_ins) == Branch:
            jump_target = last_ins.branch_addrs()[0]
            if jump_target in cfg.blocks:
                block.next_blocks.append(jump_target)
                cfg.blocks[jump_target].predecessors.append(leader)
        elif type(last_ins) == LoopEnd:
            loop_target = last_ins.branch_addrs()[0]
            if loop_target in cfg.blocks:
                block.next_blocks.append(loop_target)
                cfg.blocks[loop_target].predecessors.append(leader)
        elif type(last_ins) == BranchByDir:
            next_addr = leader + sum(inst.size for inst in block.instructions)
            if next_addr in cfg.blocks:
                block.next_blocks.append(next_addr)
                cfg.blocks[next_addr].predecessors.append(leader)

            for jump_target in last_ins.branch_addrs():
                if jump_target in cfg.blocks:
                    block.next_blocks.append(jump_target)
                    cfg.blocks[jump_target].predecessors.append(leader)
        else:
            next_addr = leader + sum(inst.size for inst in block.instructions)
            if next_addr in cfg.blocks:
                block.next_blocks.append(next_addr)
                cfg.blocks[next_addr].predecessors.append(leader)

    return cfg


def detect_if_then_else(cfg: ControlFlowGraph):
    patterns = []

    for leader, block in cfg.blocks.items():
        # Look for blocks ending with conditional jumps that have two successors
        if (len(block.instructions) > 0 and
            type(block.instructions[-1]) == BranchOnFlag and
                len(block.next_blocks) == 2):

            # One successor should be the fall-through (then block)
            # The other should be the jump target (else block)
            fallthrough_addr = leader + sum(inst.size for inst in block.instructions)
            jump_target = block.instructions[-1].branch_addrs()[0]

            if fallthrough_addr in block.next_blocks and jump_target in block.next_blocks:
                # Check if both paths eventually converge
                then_block = cfg.blocks[fallthrough_addr]
                else_block = cfg.blocks[jump_target]

                # Look for a common successor
                common_successors = set(then_block.next_blocks) & set(else_block.next_blocks)

                if common_successors:
                    join_block = cfg.blocks[list(common_successors)[0]]
                    patterns.append({
                        "if_block": leader,
                        "then_block": fallthrough_addr,
                        "else_block": jump_target,
                        "join_block": join_block.start_address
                    })

    return patterns


def detect_loop(cfg: ControlFlowGraph):
    loops = []
    verbose_debug = False

    for leader, block in cfg.blocks.items():
        if verbose_debug:
            print(f"=== BLOCK: {hex(leader)} ===")
            for ins in block.instructions:
                if type(ins) == LoopEnd:
                    print(f"[LLL]: {ins}")
                else:
                    print(f"[   ]: {ins}")
            print(f"=== BLOCK END ===")

        if len(block.instructions) > 0 and type(block.instructions[-1]) == LoopEnd:
            start_blocks = []
            for pred in block.predecessors:
                if isinstance(cfg.blocks[pred].instructions[-1], LoopStart):
                    start_blocks.append(pred)

            loop_instruction = block.instructions[-1]
            loop_header_addr = loop_instruction.addr
            loops.append({
                "loop_init": start_blocks,
                "loop_header": loop_header_addr,
                "back_edge_block": leader,
                "loop_exit_addr": leader + sum(inst.size for inst in block.instructions)
            })
    return loops
