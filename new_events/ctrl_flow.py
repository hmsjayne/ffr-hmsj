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

        # Return instructions also create leaders for the next instruction
        # (though return instructions themselves don't have successors)
        elif isinstance(code, ReturnInstruction):
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

    # Set the entry point
    if addresses:
        cfg.entry_point = addresses[0]

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
        elif isinstance(last_ins, ReturnInstruction):
            # Return instructions terminate the block with no successors
            # They are exit points from the function/event
            block.type.add("return")
        else:
            # Regular instructions: connect to the next sequential block
            next_addr = leader + sum(inst.size for inst in block.instructions)
            if next_addr in cfg.blocks:
                block.next_blocks.append(next_addr)
                cfg.blocks[next_addr].predecessors.append(leader)

    return cfg


def detect_if_then_else(cfg: ControlFlowGraph):
    """Enhanced if/then/else detection with pattern classification."""
    patterns = []

    for leader, block in cfg.blocks.items():
        # Look for blocks ending with conditional jumps that have two successors
        last_instruction = block.instructions[-1] if block.instructions else None
        is_conditional_branch = (
            isinstance(last_instruction, (BranchOnFlag, BranchOnItem, BranchOnGil)) and
            len(block.next_blocks) == 2
        )

        if is_conditional_branch:

            # One successor should be the fall-through (then block)
            # The other should be the jump target (else block)
            fallthrough_addr = leader + sum(inst.size for inst in block.instructions)
            jump_target = block.instructions[-1].branch_addrs()[0]

            if fallthrough_addr in block.next_blocks and jump_target in block.next_blocks:
                then_block = cfg.blocks[fallthrough_addr]
                else_block = cfg.blocks[jump_target]

                # Enhanced pattern analysis
                pattern_info = {
                    "type": "conditional",
                    "if_block": leader,
                    "then_block": fallthrough_addr,
                    "else_block": jump_target,
                    "condition": _extract_condition_info(last_instruction)
                }

                # Look for a common successor (join point)
                common_successors = set(then_block.next_blocks) & set(else_block.next_blocks)

                if common_successors:
                    join_addr = list(common_successors)[0]
                    pattern_info["join_block"] = join_addr
                    pattern_info["pattern_type"] = "if_then_else"

                    # Mark blocks for annotation
                    cfg.blocks[leader].type.add("conditional_branch")
                    cfg.blocks[fallthrough_addr].type.add("then_branch")
                    cfg.blocks[jump_target].type.add("else_branch")
                    cfg.blocks[join_addr].type.add("branch_join")

                elif len(then_block.next_blocks) == 0 or len(else_block.next_blocks) == 0:
                    # One branch leads to termination (return/exit)
                    pattern_info["pattern_type"] = "if_then_return"
                    pattern_info["has_early_return"] = True

                    # Mark blocks
                    cfg.blocks[leader].type.add("conditional_branch")
                    cfg.blocks[fallthrough_addr].type.add("then_branch")
                    cfg.blocks[jump_target].type.add("else_branch")

                else:
                    # Divergent paths (no obvious join)
                    pattern_info["pattern_type"] = "if_then_divergent"

                    # Mark blocks
                    cfg.blocks[leader].type.add("conditional_branch")
                    cfg.blocks[fallthrough_addr].type.add("then_branch")
                    cfg.blocks[jump_target].type.add("else_branch")

                patterns.append(pattern_info)

    return patterns


def detect_loop(cfg: ControlFlowGraph):
    """Enhanced loop detection with better pattern recognition."""
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
                if cfg.blocks[pred].instructions and isinstance(cfg.blocks[pred].instructions[-1], LoopStart):
                    start_blocks.append(pred)

            loop_instruction = block.instructions[-1]
            loop_header_addr = loop_instruction.addr

            # Enhanced loop information
            loop_info = {
                "type": "structured_loop",
                "loop_init": start_blocks,
                "loop_header": loop_header_addr,
                "back_edge_block": leader,
                "loop_exit_addr": leader + sum(inst.size for inst in block.instructions),
                "loop_body_blocks": _find_loop_body_blocks(cfg, start_blocks, leader),
                "is_nested": _is_nested_loop(cfg, start_blocks, leader)
            }

            # Mark loop-related blocks
            for init_block_addr in start_blocks:
                cfg.blocks[init_block_addr].type.add("loop_start")
            cfg.blocks[leader].type.add("loop_end")

            loops.append(loop_info)

    return loops


def _find_loop_body_blocks(cfg: ControlFlowGraph, start_blocks: list[int], back_edge_block: int) -> list[int]:
    """Find all blocks that are part of the loop body."""
    if not start_blocks:
        return []

    loop_body = set()

    # Simple approach: find blocks reachable from loop start and dominated by it
    # This is a simplified version - a full implementation would use dominance analysis
    to_visit = start_blocks.copy()
    visited = set()

    while to_visit:
        current = to_visit.pop()
        if current in visited or current == back_edge_block:
            continue

        visited.add(current)
        loop_body.add(current)

        # Add successors to visit
        if current in cfg.blocks:
            to_visit.extend(cfg.blocks[current].next_blocks)

    return sorted(list(loop_body))


def _is_nested_loop(cfg: ControlFlowGraph, start_blocks: list[int], back_edge_block: int) -> bool:
    """Check if this loop contains other loops (nested loops)."""
    loop_body = _find_loop_body_blocks(cfg, start_blocks, back_edge_block)

    # Check if any block in the loop body has loop_start or loop_end markers
    for block_addr in loop_body:
        if block_addr in cfg.blocks:
            block_types = cfg.blocks[block_addr].type
            if "loop_start" in block_types or "loop_end" in block_types:
                return True

    return False


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

            pattern_info = {
                "type": "switch",
                "pattern_type": "switch_by_direction",
                "switch_block": switch_addr,
                "case_up": case_addrs["up"],
                "case_right": case_addrs["right"],
                "case_left": case_addrs["left"],
                "case_down": case_addrs["down"],
                "join_block": join_addr,
                "unique_cases": len(unique_target_addrs),
                "total_cases": 4
            }

            # Mark blocks for annotation
            cfg.blocks[switch_addr].type.add("switch_block")

            for direction, addr in case_addrs.items():
                if addr in cfg.blocks:
                    cfg.blocks[addr].type.add(f"case_{direction}")
                    cfg.blocks[addr].type.add("switch_case")

            cfg.blocks[join_addr].type.add("switch_join")

            patterns.append(pattern_info)

    return patterns


def detect_return_blocks(cfg: ControlFlowGraph) -> list[dict]:
    """
    Detects blocks that end with return instructions.

    These blocks represent exit points from the function/event and have no successors.

    Args:
        cfg: The ControlFlowGraph to analyze.

    Returns:
        A list of dictionaries, where each dictionary contains information about
        a return block including its address and any preceding blocks.
    """
    return_blocks = []

    for block_addr, block in cfg.blocks.items():
        if "return" in block.type:
            return_blocks.append({
                "return_block": block_addr,
                "predecessors": block.predecessors.copy(),
                "instruction_count": len(block.instructions)
            })

    return return_blocks


def _extract_condition_info(instruction) -> dict:
    """Extract condition information from different branch instruction types."""
    if isinstance(instruction, BranchOnFlag):
        return {
            "branch_type": "flag",
            "flag_id": instruction.flag_id,
            "condition_type": instruction.cond
        }
    elif isinstance(instruction, BranchOnItem):
        return {
            "branch_type": "item",
            "mode": instruction.mode,
            "item_index": instruction.item_index
        }
    elif isinstance(instruction, BranchOnGil):
        return {
            "branch_type": "gil"
        }
    else:
        return {"branch_type": "unknown"}


def analyze_control_flow(cfg: ControlFlowGraph) -> dict:
    """Comprehensive control flow analysis with annotations."""
    analysis = {
        "entry_point": cfg.entry_point,
        "total_blocks": len(cfg.blocks),
        "patterns": {
            "loops": detect_loop(cfg),
            "conditionals": detect_if_then_else(cfg),
            "switches": detect_switch_by_dir(cfg),
            "returns": detect_return_blocks(cfg)
        },
        "block_types": {},
        "complexity_metrics": _calculate_complexity_metrics(cfg)
    }

    # Categorize blocks by their types
    for addr, block in cfg.blocks.items():
        analysis["block_types"][addr] = {
            "types": list(block.type),
            "instruction_count": len(block.instructions),
            "successors": len(block.next_blocks),
            "predecessors": len(block.predecessors)
        }

    return analysis


def _calculate_complexity_metrics(cfg: ControlFlowGraph) -> dict:
    """Calculate complexity metrics for the control flow graph."""
    metrics = {
        "cyclomatic_complexity": 1,  # Base complexity
        "max_nesting_depth": 0,
        "branch_points": 0,
        "exit_points": 0
    }

    # Calculate cyclomatic complexity: edges - nodes + 2 * connected_components
    edges = sum(len(block.next_blocks) for block in cfg.blocks.values())
    nodes = len(cfg.blocks)
    metrics["cyclomatic_complexity"] = edges - nodes + 2  # Assuming single connected component

    # Count various control flow elements
    for block in cfg.blocks.values():
        if len(block.next_blocks) > 1:
            metrics["branch_points"] += 1
        if len(block.next_blocks) == 0:
            metrics["exit_points"] += 1

    # Simple nesting depth estimation based on loop and conditional markers
    max_depth = 0
    for block in cfg.blocks.values():
        depth = 0
        if "loop_start" in block.type or "conditional_branch" in block.type:
            depth += 1
        if "switch_block" in block.type:
            depth += 1
        max_depth = max(max_depth, depth)

    metrics["max_nesting_depth"] = max_depth

    return metrics
