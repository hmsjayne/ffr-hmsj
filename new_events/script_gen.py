"""
Script Code Generator for Event System

This module converts Event ASTs into Python-inspired game script code that can be
easily edited by ROM hackers and then recompiled back to bytecode.

The generated script language is Python-inspired but includes game-specific
constructs and operations that map directly to Final Fantasy I event instructions.
"""

from typing import List, Dict, Any, Optional
from new_events.ast_gen import ASTNode, ASTNodeType
from new_events.instructions import BaseInstruction


class ScriptCodeGenerator:
    """Generates Python-inspired script code from Event ASTs."""

    def __init__(self):
        self.indent_level = 0
        self.lines = []
        self.symbol_table = self._build_symbol_table()

    def _build_symbol_table(self) -> Dict[str, Any]:
        """Build initial symbol table with game constants."""
        # TODO: Load from external data files
        return {
            'items': {
                # Placeholder item constants - will be populated from game data
                'LUTE': 0x1c,
                'CROWN': 0x1d,
                'CRYSTAL': 0x1e,
                'MYSTIC_KEY': 0x1f,
                # ... more items
            },
            'flags': {
                # Placeholder flag constants
                'PRINCESS_RESCUED': 0x01,
                'CORNELIAN_FREED': 0x02,
                # ... more flags
            },
            'text': {
                # Placeholder text constants
                'PRINCESS_SAVED': 0x42,
                'NOT_ENOUGH_GIL': 0x43,
                # ... more text
            }
        }

    def generate(self, ast: ASTNode) -> str:
        """Generate script code from AST."""
        self.lines = []
        self.indent_level = 0

        self._generate_node(ast)

        return '\n'.join(self.lines)

    def _generate_node(self, node: ASTNode) -> None:
        """Generate code for a specific AST node."""
        if node.node_type == ASTNodeType.PROGRAM:
            self._generate_program(node)
        elif node.node_type == ASTNodeType.SEQUENCE:
            self._generate_sequence(node)
        elif node.node_type == ASTNodeType.IF_STATEMENT:
            self._generate_if_statement(node)
        elif node.node_type == ASTNodeType.WHILE_LOOP:
            self._generate_while_loop(node)
        elif node.node_type == ASTNodeType.SWITCH_STATEMENT:
            self._generate_switch_statement(node)
        elif node.node_type == ASTNodeType.RETURN_STATEMENT:
            self._generate_return_statement(node)
        elif node.node_type == ASTNodeType.INSTRUCTION:
            self._generate_instruction(node)
        else:
            self._add_line(f"# Unknown node type: {node.node_type}")

    def _generate_program(self, node: ASTNode) -> None:
        """Generate code for the program root."""
        entry_point = node.get_metadata('entry_point')
        unreachable_blocks = node.get_metadata('unreachable_blocks', [])

        # Add header comments
        self._add_line('"""')
        self._add_line("Final Fantasy I Event Script")
        if entry_point:
            self._add_line(f"Main event starts at: {hex(entry_point)}")
        if unreachable_blocks:
            self._add_line(f"Contains {len(unreachable_blocks)} subroutines")
        self._add_line('"""')
        self._add_line("")

        # Generate main event function
        if entry_point:
            self._add_line(f"@event_function({hex(entry_point)})")
            self._add_line("def main_event():")
            self._indent()

            # Generate main sequence
            main_sequences = [child for child in node.children if not child.get_metadata('unreachable')]
            if main_sequences:
                for child in main_sequences:
                    self._generate_node(child)
            else:
                self._add_line("pass")

            self._dedent()
            self._add_line("")
            self._add_line("")

        # Generate subroutines (unreachable blocks)
        unreachable_sequences = [child for child in node.children if child.get_metadata('unreachable')]
        for i, child in enumerate(unreachable_sequences):
            if child.source_blocks:
                func_addr = child.source_blocks[0]
                self._add_line(f"@event_function({hex(func_addr)})")
                self._add_line(f"def subroutine_{func_addr:08x}():")
                self._indent()
                self._generate_node(child)
                self._dedent()
                self._add_line("")
                self._add_line("")

    def _generate_sequence(self, node: ASTNode) -> None:
        """Generate code for a sequence of statements."""
        if not node.children:
            self._add_line("pass")
            return

        for child in node.children:
            self._generate_node(child)

    def _generate_if_statement(self, node: ASTNode) -> None:
        """Generate code for if/then/else statements."""
        condition = node.get_metadata('condition', {})
        pattern_type = node.get_metadata('pattern_type', 'unknown')

        # Generate condition expression
        condition_expr = self._format_condition(condition)
        self._add_line(f"if {condition_expr}:")
        self._indent()

        # Generate then branch
        then_child = None
        else_child = None

        for child in node.children:
            branch_type = child.get_metadata('branch_type')
            if branch_type == 'then':
                then_child = child
            elif branch_type == 'else':
                else_child = child

        if then_child:
            self._generate_node(then_child)
        else:
            self._add_line("pass")

        # Generate else branch if present
        if else_child:
            self._dedent()
            self._add_line("else:")
            self._indent()
            self._generate_node(else_child)

        self._dedent()

    def _generate_while_loop(self, node: ASTNode) -> None:
        """Generate code for while loops."""
        loop_type = node.get_metadata('type', 'unknown')
        initial_count = node.get_metadata('initial_count', '?')
        step = node.get_metadata('step', '?')

        # Generate loop header - use range() for counter-based loops
        if loop_type == 'structured_loop' and initial_count != '?' and step != '?':
            # For decrementing counter loops, use range
            if step == 1:  # Decrement by 1
                self._add_line(f"for _ in range({initial_count}):")
            else:
                self._add_line(f"for _ in range({initial_count}, 0, -{step}):")
        else:
            self._add_line(f"# {loop_type}: count={initial_count}, step={step}")
            self._add_line("while True:  # TODO: Convert loop condition")

        self._indent()

        # Generate loop body
        if node.children:
            for child in node.children:
                if child.get_metadata('is_loop_body'):
                    self._generate_node(child)
                    break
            else:
                # No explicit loop body child, generate all children
                for child in node.children:
                    self._generate_node(child)
        else:
            self._add_line("pass")

        self._dedent()

    def _generate_switch_statement(self, node: ASTNode) -> None:
        """Generate code for switch statements (directional branches)."""
        # For now, convert switch to if/elif chain
        # TODO: Consider custom switch syntax for the script language

        cases = []
        for child in node.children:
            case_name = child.get_metadata('switch_case')
            if case_name:
                cases.append((case_name, child))

        if not cases:
            self._add_line("# Empty switch statement")
            return

        # Generate if/elif chain
        for i, (case_name, case_child) in enumerate(cases):
            if i == 0:
                self._add_line(f"if direction == '{case_name}':")
            else:
                self._add_line(f"elif direction == '{case_name}':")

            self._indent()
            self._generate_node(case_child)
            self._dedent()

    def _generate_return_statement(self, node: ASTNode) -> None:
        """Generate code for return statements."""
        self._add_line("return")

    def _generate_instruction(self, node: ASTNode) -> None:
        """Generate code for individual instructions."""
        instruction = node.get_metadata('instruction')
        opcode = node.get_metadata('opcode')

        if not instruction:
            self._add_line(f"# Unknown instruction")
            return

        # Map opcodes to high-level operations
        # TODO: Implement comprehensive opcode mapping
        if opcode == 0x48:  # Call
            call_addr = getattr(instruction, 'addr', None)
            if call_addr:
                self._add_line(f"subroutine_{call_addr:08x}()")
            else:
                self._add_line("# Call instruction (unknown target)")
        elif opcode == 0xc:  # Branch
            branch_addr = getattr(instruction, 'addr', None)
            self._add_line(f"# Unconditional branch to {hex(branch_addr) if branch_addr else 'unknown'}")
        else:
            # Generic instruction - preserve opcode info for now
            self._add_line(f"instruction_{opcode:02x}()  # {type(instruction).__name__}")

    def _format_condition(self, condition: Dict[str, Any]) -> str:
        """Format a condition dictionary as script code."""
        branch_type = condition.get('branch_type')

        if branch_type == 'flag':
            flag_id = condition.get('flag_id', '?')
            cond_type = condition.get('condition_type', '?')
            return f"flag[{flag_id}] == {cond_type}"
        elif branch_type == 'item':
            item_id = condition.get('item_index', '?')
            mode = condition.get('mode', '?')
            if mode == 1:  # has item
                return f"player.has_item({item_id})"
            else:
                return f"player.item_check({item_id}, mode={mode})"
        elif branch_type == 'gil':
            return "player.has_enough_gil()"  # TODO: Extract threshold
        elif branch_type == 'yesno':
            return "dialog_yes_no()"  # TODO: Extract dialog text
        else:
            return f"condition_{branch_type or 'unknown'}()"

    def _add_line(self, line: str) -> None:
        """Add a line of code with proper indentation."""
        indent = "    " * self.indent_level
        self.lines.append(indent + line)

    def _indent(self) -> None:
        """Increase indentation level."""
        self.indent_level += 1

    def _dedent(self) -> None:
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - 1)


def generate_script_from_ast(ast: ASTNode) -> str:
    """Main entry point for generating script code from AST."""
    generator = ScriptCodeGenerator()
    return generator.generate(ast)
