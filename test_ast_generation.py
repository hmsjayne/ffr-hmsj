#!/usr/bin/env python3
"""
Test script demonstrating complete AST generation capabilities.

This script creates synthetic CFGs and shows how the AST generation system
handles different control flow patterns.
"""

from new_events.instructions import *
from new_events.ctrl_flow import build_cfg, analyze_control_flow
from new_events.ast_gen import build_ast_from_analysis, print_ast

def create_complex_program():
    """Create a complex program with loops, conditionals, and switch statements."""
    program = {
        # Entry point with setup
        0x1000: GenericInstruction(opcode=0x10, size=4, params_data=b'\x00\x00'),
        
        # Loop structure: count=5, step=1
        0x1004: LoopStart(opcode=0x19, size=4, repeat_count=5),
        0x1008: GenericInstruction(opcode=0x11, size=4, params_data=b'\x00\x00'),  # loop body
        0x100c: BranchOnFlag(opcode=0x2d, size=8, flag_id=10, cond=1, addr=0x1020),  # conditional in loop
        0x1014: GenericInstruction(opcode=0x12, size=4, params_data=b'\x00\x00'),  # then branch
        0x1018: Branch(opcode=0x0c, size=8, addr=0x1024),  # skip else
        0x1020: GenericInstruction(opcode=0x13, size=4, params_data=b'\x00\x00'),  # else branch
        0x1024: LoopEnd(opcode=0x19, size=8, step=1, addr=0x1004),  # end loop
        
        # Switch statement after loop
        0x102c: BranchByDir(opcode=0x42, size=16, addr_up=0x1040, addr_right=0x1050, addr_left=0x1060),
        # Case up
        0x1040: GenericInstruction(opcode=0x20, size=4, params_data=b'\x00\x00'),
        0x1044: Branch(opcode=0x0c, size=8, addr=0x1070),  # to join
        # Case right  
        0x1050: GenericInstruction(opcode=0x21, size=4, params_data=b'\x00\x00'),
        0x1054: Branch(opcode=0x0c, size=8, addr=0x1070),  # to join
        # Case left
        0x1060: GenericInstruction(opcode=0x22, size=4, params_data=b'\x00\x00'),
        0x1064: GenericInstruction(opcode=0x23, size=4, params_data=b'\x00\x00'),
        # Case down (fall-through from switch)
        
        # Join point and return
        0x1070: GenericInstruction(opcode=0x30, size=4, params_data=b'\x00\x00'),
        0x1074: ReturnInstruction(opcode=0x0, size=4, params_data=b'\x00\x00')
    }
    return program

def test_simple_conditional():
    """Test basic if/then/else pattern."""
    print("=== Simple Conditional Test ===")
    
    program = {
        0x2000: BranchOnFlag(opcode=0x2d, size=8, flag_id=1, cond=2, addr=0x2010),
        0x2008: GenericInstruction(opcode=0x10, size=4, params_data=b'\x00\x00'),  # then
        0x200c: Branch(opcode=0x0c, size=8, addr=0x2018),  # to join
        0x2010: GenericInstruction(opcode=0x11, size=4, params_data=b'\x00\x00'),  # else
        0x2014: GenericInstruction(opcode=0x12, size=4, params_data=b'\x00\x00'),
        0x2018: ReturnInstruction(opcode=0x0, size=4, params_data=b'\x00\x00')   # join + return
    }
    
    cfg = build_cfg(program)
    analysis = analyze_control_flow(cfg)
    ast = build_ast_from_analysis(cfg, analysis)
    
    print_ast(ast)
    print()

def test_nested_loops():
    """Test nested loop structures."""
    print("=== Nested Loops Test ===")
    
    program = {
        # Outer loop: count=3, step=1  
        0x3000: LoopStart(opcode=0x19, size=4, repeat_count=3),
        0x3004: GenericInstruction(opcode=0x10, size=4, params_data=b'\x00\x00'),  # outer body
        
        # Inner loop: count=2, step=1
        0x3008: LoopStart(opcode=0x19, size=4, repeat_count=2),
        0x300c: GenericInstruction(opcode=0x11, size=4, params_data=b'\x00\x00'),  # inner body
        0x3010: LoopEnd(opcode=0x19, size=8, step=1, addr=0x3008),  # end inner
        
        0x3018: GenericInstruction(opcode=0x12, size=4, params_data=b'\x00\x00'),  # more outer body
        0x301c: LoopEnd(opcode=0x19, size=8, step=1, addr=0x3000),  # end outer
        
        0x3024: ReturnInstruction(opcode=0x0, size=4, params_data=b'\x00\x00')
    }
    
    cfg = build_cfg(program)
    analysis = analyze_control_flow(cfg)
    ast = build_ast_from_analysis(cfg, analysis)
    
    print_ast(ast)
    print()

def test_complex_program():
    """Test the complete complex program."""
    print("=== Complex Program Test ===")
    
    program = create_complex_program()
    cfg = build_cfg(program)
    analysis = analyze_control_flow(cfg)
    ast = build_ast_from_analysis(cfg, analysis)
    
    print("Control Flow Summary:")
    print(f"  Total blocks: {analysis['total_blocks']}")
    print(f"  Loops: {len(analysis['patterns']['loops'])}")
    print(f"  Conditionals: {len(analysis['patterns']['conditionals'])}")
    print(f"  Switches: {len(analysis['patterns']['switches'])}")
    print(f"  Returns: {len(analysis['patterns']['returns'])}")
    print(f"  Complexity: {analysis['complexity_metrics']}")
    print()
    
    print("Generated AST:")
    print_ast(ast)
    print()

def main():
    print("=== AST Generation Test Suite ===\n")
    
    test_simple_conditional()
    test_nested_loops()
    test_complex_program()
    
    print("=== All Tests Completed ===")

if __name__ == "__main__":
    main()
