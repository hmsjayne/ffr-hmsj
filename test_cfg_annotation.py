#!/usr/bin/env python3
"""
Test script demonstrating the enhanced CFG annotation system.

This script creates synthetic instruction patterns and shows how the CFG
annotation system identifies and categorizes different control flow patterns.
"""

from new_events.instructions import *
from new_events.ctrl_flow import build_cfg, analyze_control_flow

def create_test_program():
    """Create a test program with various control flow patterns."""
    program = {
        # Simple if/then/else pattern
        0x1000: BranchOnFlag(opcode=0x2d, size=8, flag_id=5, cond=1, addr=0x1020),
        0x1008: GenericInstruction(opcode=0x10, size=4, params_data=b'\x00\x00'),  # then block
        0x100c: Branch(opcode=0x0c, size=8, addr=0x1030),  # jump to join
        0x1020: GenericInstruction(opcode=0x11, size=4, params_data=b'\x00\x00'),  # else block
        0x1024: GenericInstruction(opcode=0x12, size=4, params_data=b'\x00\x00'),
        0x1028: GenericInstruction(opcode=0x13, size=4, params_data=b'\x00\x00'),
        
        # Join point
        0x1030: GenericInstruction(opcode=0x14, size=4, params_data=b'\x00\x00'),
        
        # Loop pattern
        0x1034: LoopStart(opcode=0x19, size=4, repeat_count=10),
        0x1038: GenericInstruction(opcode=0x15, size=4, params_data=b'\x00\x00'),  # loop body
        0x103c: GenericInstruction(opcode=0x16, size=4, params_data=b'\x00\x00'),
        0x1040: LoopEnd(opcode=0x19, size=8, step=1, addr=0x1034),
        
        # Return instruction
        0x1048: ReturnInstruction(opcode=0x0, size=4, params_data=b'\x00\x00')
    }
    return program

def main():
    print("=== CFG Annotation System Test ===\n")
    
    # Create test program
    program = create_test_program()
    print("Created test program with:")
    print("- If/then/else conditional")
    print("- Structured loop")
    print("- Return instruction")
    print()
    
    # Build CFG
    cfg = build_cfg(program)
    print(f"Built CFG with {len(cfg.blocks)} basic blocks\n")
    
    # Perform comprehensive analysis
    analysis = analyze_control_flow(cfg)
    
    # Display results
    print("=== Analysis Results ===")
    print(f"Entry Point: {hex(analysis['entry_point'])}")
    print(f"Total Blocks: {analysis['total_blocks']}")
    print(f"Complexity Metrics: {analysis['complexity_metrics']}")
    print()
    
    # Show pattern detection
    print("=== Detected Patterns ===")
    
    loops = analysis['patterns']['loops']
    print(f"Loops detected: {len(loops)}")
    for i, loop in enumerate(loops):
        print(f"  Loop {i+1}: {loop['type']}")
        print(f"    Init blocks: {[hex(x) for x in loop['loop_init']]}")
        print(f"    Header: {hex(loop['loop_header'])}")
        print(f"    Body blocks: {[hex(x) for x in loop['loop_body_blocks']]}")
    
    conditionals = analysis['patterns']['conditionals']
    print(f"\nConditionals detected: {len(conditionals)}")
    for i, cond in enumerate(conditionals):
        print(f"  Conditional {i+1}: {cond['pattern_type']}")
        print(f"    If block: {hex(cond['if_block'])}")
        print(f"    Then block: {hex(cond['then_block'])}")
        print(f"    Else block: {hex(cond['else_block'])}")
        if 'join_block' in cond:
            print(f"    Join block: {hex(cond['join_block'])}")
    
    returns = analysis['patterns']['returns']
    print(f"\nReturn blocks detected: {len(returns)}")
    for i, ret in enumerate(returns):
        print(f"  Return {i+1}: {hex(ret['return_block'])}")
        print(f"    Predecessors: {[hex(x) for x in ret['predecessors']]}")
    
    # Show block annotations
    print("\n=== Block Annotations ===")
    for addr, block_info in analysis['block_types'].items():
        if len(block_info['types']) > 1:  # Show interesting blocks
            print(f"  {hex(addr)}: {block_info['types']}")
    
    print("\n=== Test Completed Successfully ===")

if __name__ == "__main__":
    main()
