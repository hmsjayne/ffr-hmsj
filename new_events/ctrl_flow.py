from collections import OrderedDict
from typing import Optional
from new_events.instructions import *


class BasicBlock:
    def __init__(self, start_address: int):
        self.start_address: int = start_address
        self.instructions: list[BaseInstruction] = []
        self.next_blocks: list[int] = []
        self.predecessors: list[int] = []
        self.type: set[str] = {"basic"}


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
        last_ins = block.instructions[-1]

        if isinstance(last_ins, BaseBranch):
            for jump_target in last_ins.branch_addrs():
                if jump_target in cfg.blocks:
                    block.next_blocks.append(jump_target)
                    cfg.blocks[jump_target].predecessors.append(leader)

            # Conditional branches will branch on some condition and continue
            # on other conditions. An unconditional branch is the only
            # exemption to this.
            if type(last_ins) != Branch:
                next_addr = leader + sum(inst.size for inst in block.instructions)

                if next_addr in cfg.blocks:
                    block.next_blocks.append(next_addr)
                    cfg.blocks[next_addr].predecessors.append(leader)
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


def detect_switch_by_dir(cfg: ControlFlowGraph) -> list[dict]:
    """
    Detects a switch-like control flow structure based on the BranchByDir instruction.

    This pattern consists of:
    1. A "switch" block that ends with a BranchByDir instruction.
    2. Four potential "case" blocks corresponding to 'up', 'right', 'left', and 'down'.
    3. A single "join" block where all execution paths from the case blocks converge.

    Args:
        cfg: The ControlFlowGraph to analyze.

    Returns:
        A list of dictionaries, where each dictionary represents a detected
        switch pattern and contains the addresses of the switch, case, and join blocks.
    """
    patterns = []

    for switch_addr, switch_block in cfg.blocks.items():
        # 1. Find a block ending with BranchByDir
        if not switch_block.instructions:
            continue

        last_ins = switch_block.instructions[-1]
        if not isinstance(last_ins, BranchByDir):
            continue

        # 2. Identify the addresses for all four "case" blocks
        # The 'down' case is the fall-through block
        fallthrough_addr = switch_addr + sum(inst.size for inst in switch_block.instructions)

        case_addrs = {
            "up": last_ins.addr_up,
            "right": last_ins.addr_right,
            "left": last_ins.addr_left,
            "down": fallthrough_addr,
        }

        # Collect the unique, valid blocks that the switch can branch to.
        # It's common for 'left' and 'right' to be the same, for instance.
        unique_target_addrs = {addr for addr in case_addrs.values() if addr in cfg.blocks}

        if not unique_target_addrs:
            continue  # This switch leads nowhere valid.

        # 3. Find the common "join" block
        # We find the set of successors for each unique case block.
        # The intersection of these sets will give us the common join block.
        successor_sets = []
        for target_addr in unique_target_addrs:
            target_block = cfg.blocks[target_addr]

            # A valid case must lead somewhere. If it has no successors, the
            # paths don't converge.
            if not target_block.next_blocks:
                successor_sets = []  # Invalidate to prevent finding a pattern
                break

            successor_sets.append(set(target_block.next_blocks))

        # If we couldn't get successors for all paths, skip.
        if not successor_sets:
            continue

        # Calculate the intersection of all successor sets
        common_successors = successor_sets[0].copy()
        for s_set in successor_sets[1:]:
            common_successors.intersection_update(s_set)

        # 4. If we found exactly one common successor, we've found the pattern
        if len(common_successors) == 1:
            join_addr = common_successors.pop()
            patterns.append({
                "switch_block": switch_addr,
                "case_up": case_addrs["up"],
                "case_right": case_addrs["right"],
                "case_left": case_addrs["left"],
                "case_down": case_addrs["down"],
                "join_block": join_addr,
            })

    return patterns
