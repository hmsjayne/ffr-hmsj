#!/usr/bin/env python3
"""
AST Generation for Event System

This module converts annotated Control Flow Graphs (CFGs) into Abstract Syntax Trees (ASTs)
that can be used to generate Python-like event scripts.

The AST generation process:
1. Takes an annotated CFG from ctrl_flow.py
2. Identifies high-level control structures (loops, conditionals, etc.)
3. Builds a hierarchical AST representation
4. Preserves semantic meaning while abstracting away low-level control flow

Loop Structure Understanding:
- All loops use instruction 0x19 (loop command)
- 4-byte version (LoopStart): Sets initial counter value
- 8-byte version (LoopEnd): Decrements counter by step and jumps if counter >= 0
- Pattern: count = initial_value; while count >= 0: body; count -= step
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Union
from enum import Enum

from new_events.ctrl_flow import ControlFlowGraph, BasicBlock
from new_events.instructions import BaseInstruction, ReturnInstruction, GenericInstruction, LoopStart, LoopEnd


class ASTNodeType(Enum):
    """Types of AST nodes."""
    PROGRAM = "program"
    SEQUENCE = "sequence"
    IF_STATEMENT = "if_statement"
    WHILE_LOOP = "while_loop"
    SWITCH_STATEMENT = "switch_statement"
    RETURN_STATEMENT = "return_statement"
    EXPRESSION = "expression"
    INSTRUCTION = "instruction"


@dataclass
class ASTNode:
    """Base class for all AST nodes."""
    node_type: ASTNodeType
    children: List['ASTNode']
    metadata: Dict[str, Any]
    source_blocks: List[int]  # Original CFG block addresses
    
    def add_child(self, child: 'ASTNode'):
        """Add a child node."""
        self.children.append(child)
    
    def get_metadata(self, key: str, default=None):
        """Get metadata value."""
        return self.metadata.get(key, default)


@dataclass
class ProgramNode(ASTNode):
    """Root node representing the entire program/event."""
    def __init__(self, entry_point: int):
        super().__init__(
            node_type=ASTNodeType.PROGRAM,
            children=[],
            metadata={"entry_point": entry_point},
            source_blocks=[]
        )


@dataclass
class SequenceNode(ASTNode):
    """Node representing a sequence of statements."""
    def __init__(self, blocks: List[int]):
        super().__init__(
            node_type=ASTNodeType.SEQUENCE,
            children=[],
            metadata={},
            source_blocks=blocks
        )


@dataclass
class IfStatementNode(ASTNode):
    """Node representing an if/then/else statement."""
    def __init__(self, condition_block: int, condition_info: Dict[str, Any]):
        super().__init__(
            node_type=ASTNodeType.IF_STATEMENT,
            children=[],  # Will contain [then_branch, else_branch] (condition is in metadata)
            metadata={
                "condition": condition_info,
                "pattern_type": "if_then_else"
            },
            source_blocks=[condition_block]
        )


@dataclass
class WhileLoopNode(ASTNode):
    """Node representing a while loop with counter-based structure."""
    def __init__(self, loop_start_block: int, loop_info: Dict[str, Any]):
        super().__init__(
            node_type=ASTNodeType.WHILE_LOOP,
            children=[],  # Will contain [body]
            metadata={
                **loop_info,
                "loop_type": "counter_loop"
            },
            source_blocks=[loop_start_block]
        )


@dataclass
class SwitchStatementNode(ASTNode):
    """Node representing a switch statement."""
    def __init__(self, switch_block: int, switch_info: Dict[str, Any]):
        super().__init__(
            node_type=ASTNodeType.SWITCH_STATEMENT,
            children=[],  # Will contain case nodes
            metadata=switch_info,
            source_blocks=[switch_block]
        )


@dataclass
class ReturnStatementNode(ASTNode):
    """Node representing a return statement."""
    def __init__(self, return_block: int, return_info: Dict[str, Any]):
        super().__init__(
            node_type=ASTNodeType.RETURN_STATEMENT,
            children=[],
            metadata=return_info,
            source_blocks=[return_block]
        )


@dataclass
class InstructionNode(ASTNode):
    """Node representing a low-level instruction."""
    def __init__(self, instruction: BaseInstruction, block_addr: int):
        super().__init__(
            node_type=ASTNodeType.INSTRUCTION,
            children=[],
            metadata={
                "instruction": instruction,
                "opcode": instruction.opcode,
                "size": instruction.size
            },
            source_blocks=[block_addr]
        )


class ASTBuilder:
    """Builds AST from annotated CFG."""
    
    def __init__(self, cfg: ControlFlowGraph, analysis: Dict[str, Any]):
        self.cfg = cfg
        self.analysis = analysis
        self.visited_blocks = set()
        self.ast_cache = {}  # Cache for blocks we've already converted
        self.loop_structures = self._identify_loop_structures()
    
    def _identify_loop_structures(self) -> Dict[int, Dict[str, Any]]:
        """Identify and analyze loop structures with their start/end instructions."""
        loop_structures = {}
        
        for loop_info in self.analysis['patterns']['loops']:
            # Extract loop details
            init_blocks = loop_info.get('loop_init', [])
            header_addr = loop_info.get('loop_header', 0)
            back_edge_block = loop_info.get('back_edge_block', 0)
            
            # Find the actual LoopStart and LoopEnd instructions
            loop_start_inst = None
            loop_end_inst = None
            
            # Look for LoopStart instruction in init blocks
            for init_block_addr in init_blocks:
                if init_block_addr in self.cfg.blocks:
                    block = self.cfg.blocks[init_block_addr]
                    for inst in block.instructions:
                        if isinstance(inst, LoopStart):
                            loop_start_inst = inst
                            break
            
            # Look for LoopEnd instruction in back edge block
            if back_edge_block in self.cfg.blocks:
                block = self.cfg.blocks[back_edge_block]
                for inst in block.instructions:
                    if isinstance(inst, LoopEnd):
                        loop_end_inst = inst
                        break
            
            # Store loop structure info
            if init_blocks:
                # Ensure we use the actual integer address, not hex strings
                init_block_key = init_blocks[0]
                if isinstance(init_block_key, str):
                    init_block_key = int(init_block_key, 16)
                    
                loop_structures[init_block_key] = {
                    "loop_info": loop_info,
                    "loop_start_inst": loop_start_inst,
                    "loop_end_inst": loop_end_inst,
                    "init_blocks": init_blocks,
                    "header_addr": header_addr,
                    "back_edge_block": back_edge_block
                }
        
        return loop_structures
    
    def build_ast(self) -> ProgramNode:
        """Build the complete AST from the CFG."""
        if not self.cfg.entry_point:
            raise ValueError("CFG has no entry point")
        
        # Create program root
        program = ProgramNode(self.cfg.entry_point)
        
        # Build the main sequence starting from entry point
        main_sequence = self._build_sequence_from_block(self.cfg.entry_point)
        if main_sequence:
            program.add_child(main_sequence)
        
        # Check for unreachable blocks and add them as separate sequences
        unreachable_blocks = set(self.cfg.blocks.keys()) - self.visited_blocks
        if unreachable_blocks:
            program.metadata["unreachable_blocks"] = sorted(list(unreachable_blocks))
            
            # Optionally build AST for unreachable code (for debugging)
            for unreachable_start in sorted(unreachable_blocks):
                if unreachable_start not in self.visited_blocks:
                    unreachable_sequence = self._build_sequence_from_block(unreachable_start)
                    if unreachable_sequence:
                        unreachable_sequence.metadata["unreachable"] = True
                        program.add_child(unreachable_sequence)
        
        return program
    
    def _build_sequence_from_block(self, start_block: int) -> Optional[ASTNode]:
        """Build a sequence of statements starting from the given block."""
        if start_block in self.visited_blocks:
            return None
        
        current_block = start_block
        sequence_children = []
        
        while current_block and current_block not in self.visited_blocks:
            block = self.cfg.blocks.get(current_block)
            if not block:
                break
            
            self.visited_blocks.add(current_block)
            
            # Check what kind of control structure this block represents
            node = self._analyze_block_for_ast_node(current_block, block)
            
            if node:
                sequence_children.append(node)
                
                # Determine next block based on node type
                if node.node_type in [ASTNodeType.IF_STATEMENT, ASTNodeType.WHILE_LOOP, 
                                     ASTNodeType.SWITCH_STATEMENT]:
                    # These structures handle their own control flow
                    # For loops, we need to find the exit point
                    if node.node_type == ASTNodeType.WHILE_LOOP:
                        # Loop exit is after the loop end block
                        loop_structure = self.loop_structures.get(current_block)
                        if loop_structure:
                            back_edge_block = loop_structure.get('back_edge_block')
                            if back_edge_block and back_edge_block in self.cfg.blocks:
                                # Find blocks after the back edge block
                                back_edge_cfg_block = self.cfg.blocks[back_edge_block]
                                if back_edge_cfg_block.next_blocks:
                                    # The exit is typically the fall-through from the loop end
                                    for next_block in back_edge_cfg_block.next_blocks:
                                        if next_block != loop_structure.get('header_addr'):
                                            current_block = next_block
                                            break
                                    else:
                                        break  # No exit found
                                else:
                                    break  # No successors
                            else:
                                break  # No back edge block
                        else:
                            break  # No loop structure info
                    else:
                        break
                elif node.node_type == ASTNodeType.RETURN_STATEMENT:
                    # Return terminates the sequence
                    break
            
            # Move to next sequential block
            if len(block.next_blocks) == 1:
                current_block = block.next_blocks[0]
            else:
                # Multiple successors or no successors - end this sequence
                break
        
        if sequence_children:
            sequence = SequenceNode([start_block])
            for child in sequence_children:
                sequence.add_child(child)
            return sequence
        
        return None
    
    def _analyze_block_for_ast_node(self, block_addr: int, block: BasicBlock) -> Optional[ASTNode]:
        """Analyze a block and create the appropriate AST node."""
        
        # Check for loop start first (highest priority since it affects control flow)
        if block_addr in self.loop_structures:
            return self._build_loop_statement(block_addr)
        # Check for other control flow patterns
        elif "conditional_branch" in block.type:
            return self._build_if_statement(block_addr)
        elif "switch_block" in block.type:
            return self._build_switch_statement(block_addr)
        elif "return" in block.type:
            return self._build_return_statement(block_addr, block)
        else:
            # Regular instruction block
            return self._build_instruction_sequence(block_addr, block)
    
    def _build_if_statement(self, condition_block: int) -> Optional[IfStatementNode]:
        """Build an if statement AST node."""
        
        # Find the conditional pattern this block belongs to
        conditional_info = None
        for pattern in self.analysis['patterns']['conditionals']:
            if pattern['if_block'] == condition_block:
                conditional_info = pattern
                break
        
        if not conditional_info:
            return None
        
        # Create if statement node
        if_node = IfStatementNode(condition_block, conditional_info.get('condition', {}))
        if_node.metadata["pattern_type"] = conditional_info.get('pattern_type', 'unknown')
        
        # Build then branch
        then_block_addr = conditional_info.get('then_block')
        if then_block_addr and then_block_addr not in self.visited_blocks:
            then_node = self._build_sequence_from_block(then_block_addr)
            if then_node:
                then_node.metadata["branch_type"] = "then"
                if_node.add_child(then_node)
        
        # Build else branch
        else_block_addr = conditional_info.get('else_block')
        if else_block_addr and else_block_addr not in self.visited_blocks:
            else_node = self._build_sequence_from_block(else_block_addr)
            if else_node:
                else_node.metadata["branch_type"] = "else"
                if_node.add_child(else_node)
        
        return if_node
    
    def _build_loop_statement(self, loop_start_block: int) -> Optional[WhileLoopNode]:
        """Build a loop statement AST node with proper counter-based semantics."""
        
        loop_structure = self.loop_structures.get(loop_start_block)
        if not loop_structure:
            return None
        
        loop_start_inst = loop_structure["loop_start_inst"]
        loop_end_inst = loop_structure["loop_end_inst"]
        loop_info = loop_structure["loop_info"]
        
        # Create loop node with counter information
        loop_node = WhileLoopNode(loop_start_block, loop_info)
        
        # Add loop counter metadata
        if loop_start_inst:
            loop_node.metadata["initial_count"] = loop_start_inst.repeat_count
        if loop_end_inst:
            loop_node.metadata["step"] = loop_end_inst.step
            loop_node.metadata["header_addr"] = loop_end_inst.addr
        
        # Build loop body - this is the tricky part
        body_blocks = loop_info.get('loop_body_blocks', [])
        if body_blocks:
            # The body starts after the loop start instruction and goes until the loop end
            body_start = None
            
            # Find the first block after the loop start
            start_block = self.cfg.blocks[loop_start_block]
            if start_block.next_blocks:
                body_start = start_block.next_blocks[0]
            
            if body_start and body_start not in self.visited_blocks:
                body_sequence = self._build_sequence_from_block(body_start)
                if body_sequence:
                    body_sequence.metadata["is_loop_body"] = True
                    loop_node.add_child(body_sequence)
        
        return loop_node
    
    def _build_switch_statement(self, switch_block: int) -> Optional[SwitchStatementNode]:
        """Build a switch statement AST node."""
        
        # Find the switch pattern this block belongs to
        switch_info = None
        for pattern in self.analysis['patterns']['switches']:
            if pattern['switch_block'] == switch_block:
                switch_info = pattern
                break
        
        if not switch_info:
            return None
        
        # Create switch node
        switch_node = SwitchStatementNode(switch_block, switch_info)
        
        # Build case branches
        cases = [
            ('case_up', 'up'),
            ('case_right', 'right'), 
            ('case_left', 'left'),
            ('case_down', 'down')
        ]
        
        for case_key, case_name in cases:
            case_addr = switch_info.get(case_key)
            if case_addr and case_addr not in self.visited_blocks:
                case_sequence = self._build_sequence_from_block(case_addr)
                if case_sequence:
                    case_sequence.metadata["switch_case"] = case_name
                    case_sequence.metadata["case_addr"] = case_addr
                    switch_node.add_child(case_sequence)
        
        return switch_node
    
    def _build_return_statement(self, return_block: int, block: BasicBlock) -> ReturnStatementNode:
        """Build a return statement AST node."""
        
        # Find return info
        return_info = None
        for pattern in self.analysis['patterns']['returns']:
            if pattern['return_block'] == return_block:
                return_info = pattern
                break
        
        if not return_info:
            return_info = {
                "return_block": return_block, 
                "predecessors": [], 
                "instruction_count": len(block.instructions)
            }
        
        return ReturnStatementNode(return_block, return_info)
    
    def _build_instruction_sequence(self, block_addr: int, block: BasicBlock) -> Optional[SequenceNode]:
        """Build a sequence of instruction nodes from a basic block."""
        
        sequence = SequenceNode([block_addr])
        
        for instruction in block.instructions:
            if not isinstance(instruction, (ReturnInstruction, LoopStart, LoopEnd)):  
                # Skip instructions that are handled as control structures
                inst_node = InstructionNode(instruction, block_addr)
                sequence.add_child(inst_node)
        
        return sequence if sequence.children else None


def build_ast_from_analysis(cfg: ControlFlowGraph, analysis: Dict[str, Any]) -> ProgramNode:
    """Main entry point for building AST from CFG analysis."""
    builder = ASTBuilder(cfg, analysis)
    return builder.build_ast()


def print_ast(node: ASTNode, indent: int = 0) -> None:
    """Debug function to print AST structure."""
    prefix = "  " * indent
    
    if node.node_type == ASTNodeType.PROGRAM:
        entry_point = hex(node.get_metadata('entry_point', 0))
        unreachable = node.get_metadata('unreachable_blocks', [])
        unreachable_info = f", unreachable: {len(unreachable)} blocks" if unreachable else ""
        print(f"{prefix}Program (entry: {entry_point}{unreachable_info})")
    elif node.node_type == ASTNodeType.SEQUENCE:
        blocks = [hex(x) for x in node.source_blocks]
        branch_type = node.get_metadata('branch_type')
        case_info = node.get_metadata('switch_case')
        extra_info = ""
        if branch_type:
            extra_info += f" [{branch_type} branch]"
        if case_info:
            extra_info += f" [case: {case_info}]"
        if node.get_metadata('is_loop_body'):
            extra_info += " [loop body]"
        if node.get_metadata('unreachable'):
            extra_info += " [UNREACHABLE]"
        print(f"{prefix}Sequence (blocks: {blocks}){extra_info}")
    elif node.node_type == ASTNodeType.IF_STATEMENT:
        pattern = node.get_metadata('pattern_type', 'unknown')
        condition = node.get_metadata('condition', {})
        flag_id = condition.get('flag_id', '?')
        cond_type = condition.get('condition_type', '?')
        print(f"{prefix}If Statement ({pattern}) - flag {flag_id}, type {cond_type}")
    elif node.node_type == ASTNodeType.WHILE_LOOP:
        loop_type = node.get_metadata('type', 'unknown')
        initial_count = node.get_metadata('initial_count', '?')
        step = node.get_metadata('step', '?')
        print(f"{prefix}While Loop ({loop_type}) - count={initial_count}, step={step}")
    elif node.node_type == ASTNodeType.SWITCH_STATEMENT:
        pattern = node.get_metadata('pattern_type', 'unknown')
        unique_cases = node.get_metadata('unique_cases', '?')
        total_cases = node.get_metadata('total_cases', '?')
        print(f"{prefix}Switch Statement ({pattern}) - {unique_cases}/{total_cases} cases")
    elif node.node_type == ASTNodeType.RETURN_STATEMENT:
        block = node.source_blocks[0] if node.source_blocks else 0
        inst_count = node.get_metadata('instruction_count', 0)
        print(f"{prefix}Return Statement (from {hex(block)}, {inst_count} instructions)")
    elif node.node_type == ASTNodeType.INSTRUCTION:
        instruction = node.get_metadata('instruction')
        opcode = node.get_metadata('opcode', '?')
        print(f"{prefix}Instruction (opcode: {hex(opcode)}) - {type(instruction).__name__}")
    else:
        print(f"{prefix}{node.node_type} - {len(node.children)} children")
    
    # Print children
    for child in node.children:
        print_ast(child, indent + 1)
