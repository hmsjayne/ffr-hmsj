from collections import OrderedDict, defaultdict, namedtuple
import pprint

Branch = namedtuple("Branch", "opcode, size, addr")
Loop = namedtuple("Loop", "opcode, size, step, addr")
BranchOnFlag = namedtuple("BranchOnFlag", "opcode, size, flag_id, cond, addr")
BranchByDir = namedtuple("BranchByDir", "opcode, size, addr_up, addr_right, addr_left")
Call = namedtuple("Call", "opcode, size, addr")


class BasicBlock:
    def __init__(self, start_address):
        self.start_address = start_address
        self.instructions = []
        self.next_blocks = []
        self.predecessors = []
        self.type = "basic"


class ControlFlowGraph:
    def __init__(self):
        self.blocks = OrderedDict()  # start_address -> BasicBlock
        self.entry_point = None


def parse_jump_target(code: tuple) -> int:
    if type(code) == Branch:
        return code.addr
    elif type(code) == BranchOnFlag:
        return code.addr
    elif type(code) == Call:
        return code.addr
    else:
        raise LookupError(f"{type(code)} in set but not?")


def build_cfg(program: dict[int, tuple]) -> ControlFlowGraph:
    cfg = ControlFlowGraph()
    addresses = sorted(program.keys())

    # Identify block leaders (start of basic blocks)
    leaders = set()
    leaders.add(addresses[0])  # Program entry point

    for addr, code in program.items():
        # Jump instructions create new leaders at their targets
        if type(code) in (Branch, BranchOnFlag, Call):
            jump_target = parse_jump_target(code)
            leaders.add(jump_target)

            # Instructions after jumps are also leaders
            next_addr = addr + code[1]
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
            current_addr += program[current_addr][1]

        cfg.blocks[leader] = block

    # Connect blocks
    for leader, block in cfg.blocks.items():
        last_instruction = block.instructions[-1]
        last_ins = last_instruction

        if type(last_ins) == BranchOnFlag:
            jump_target = parse_jump_target(last_instruction)
            next_addr = leader + sum(inst[1] for inst in block.instructions)

            if jump_target in cfg.blocks:
                block.next_blocks.append(jump_target)
                cfg.blocks[jump_target].predecessors.append(leader)

            if next_addr in cfg.blocks:
                block.next_blocks.append(next_addr)
                cfg.blocks[next_addr].predecessors.append(leader)

        elif type(last_ins) == Branch:
            jump_target = parse_jump_target(last_instruction)
            if jump_target in cfg.blocks:
                block.next_blocks.append(jump_target)
                cfg.blocks[jump_target].predecessors.append(leader)
        else:
            # Fall-through to next block
            next_addr = leader + sum(inst[1] for inst in block.instructions)
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
            fallthrough_addr = leader + sum(inst[1] for inst in block.instructions)
            jump_target = parse_jump_target(block.instructions[-1])

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
