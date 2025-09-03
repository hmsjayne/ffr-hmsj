import struct
from typing import ClassVar, Set, List
from dataclasses import dataclass, fields


@dataclass(frozen=True)
class BaseInstruction:
    """
    A base class for all instructions providing a rich, debug-friendly
    representation and common properties.

    Uses dataclasses for immutability and standard inheritance. It is
    intended as a base class and should not be instantiated directly.
    """
    opcode: int
    size: int

    _DECIMAL_FIELDS: ClassVar[Set[str]] = {'size'}

    @property
    def params(self) -> tuple:
        """Returns all instruction fields beyond opcode and size as a tuple."""
        field_names = [f.name for f in fields(self)]
        return tuple(getattr(self, name) for name in field_names[2:])

    def __repr__(self) -> str:
        """
        Generates a string representation of the instruction, formatting
        fields according to the _DECIMAL_FIELDS specification.
        """
        cls_name = self.__class__.__name__
        decimal_fields = getattr(self, '_DECIMAL_FIELDS', set())

        field_parts = []
        for field in fields(self):
            value = getattr(self, field.name)
            if field.name in decimal_fields:
                formatted_value = str(value)
            elif isinstance(value, int):
                formatted_value = f"0x{value:02x}"
            else:
                # The default repr() for bytes (e.g., b'\xff\xff') is clear
                # and appropriate for a generic representation.
                formatted_value = repr(value)

            field_parts.append(f"{field.name}={formatted_value}")

        return f"{cls_name}({', '.join(field_parts)})"


@dataclass(frozen=True, repr=False)
class BaseBranch(BaseInstruction):
    """An abstract base for any instruction that alters control flow."""

    def branch_addrs(self) -> List[int]:
        raise NotImplementedError(...)


# --- Concrete Instruction Implementations ---

@dataclass(frozen=True, repr=False)
class GenericInstruction(BaseInstruction):
    """A generic instruction for opcodes that are not explicitly defined."""
    params_data: bytes


@dataclass(frozen=True, repr=False)
class Branch(BaseBranch):
    addr: int

    def branch_addrs(self) -> List[int]:
        return [self.addr]


@dataclass(frozen=True, repr=False)
class LoopStart(BaseInstruction):
    repeat_count: int
    _DECIMAL_FIELDS = BaseInstruction._DECIMAL_FIELDS | {'repeat_count'}


@dataclass(frozen=True, repr=False)
class LoopEnd(BaseBranch):
    step: int
    addr: int
    _DECIMAL_FIELDS = BaseInstruction._DECIMAL_FIELDS | {'step'}

    def branch_addrs(self) -> List[int]:
        return [self.addr]


@dataclass(frozen=True, repr=False)
class BranchOnFlag(BaseBranch):
    flag_id: int
    cond: int
    addr: int
    _DECIMAL_FIELDS = BaseInstruction._DECIMAL_FIELDS | {'flag_id'}

    def branch_addrs(self) -> List[int]:
        return [self.addr]


@dataclass(frozen=True, repr=False)
class BranchByDir(BaseBranch):
    addr_up: int
    addr_right: int
    addr_left: int

    def branch_addrs(self) -> List[int]:
        return [self.addr_up, self.addr_right, self.addr_left]


@dataclass(frozen=True, repr=False)
class Call(BaseBranch):
    addr: int

    def branch_addrs(self) -> List[int]:
        return [self.addr]


# --- Updated Creator Functions ---

def create_branch(ins: bytes) -> Branch:
    """Example creator function for a known instruction."""
    unpacked = struct.unpack("<BBxxI", ins)
    return Branch(*unpacked)


def fallback_creator(ins: bytearray) -> tuple[GenericInstruction, None]:
    """
    Creator for unknown instructions. It preserves the raw parameter data.
    """
    if len(ins) < 2:
        raise ValueError("Instruction data is too short for header.")

    opcode = ins[0]
    size = ins[1]

    if len(ins) < size:
        raise ValueError(f"Instruction size is {size} but only {len(ins)} bytes provided.")

    # The parameters are the bytes following the header (opcode, size)
    # up to the total size of the instruction.
    params_bytes = bytes(ins[2:size])

    fallback_ins = GenericInstruction(opcode, size, params_bytes)
    return fallback_ins, None
