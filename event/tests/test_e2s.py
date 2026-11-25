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

"""Tests for the e2s module. """

import contextlib
import io
import struct
import unittest

from doslib.rom import Rom
from event.e2s import disassemble, lookup_event


def _rom_with_pointer(table_offset: int, pointer: int) -> Rom:
    data = bytearray(0x8000)
    struct.pack_into("<I", data, table_offset, pointer)
    return Rom(data)


class TestLookupEvent(unittest.TestCase):

    def test_last_soul_of_chaos_event(self):
        # 0x2495 is the last entry before the map event table at 0x7050.
        rom = _rom_with_pointer(0x6A98 + (0x2495 - 0x2328) * 4, 0x08123456)
        self.assertEqual(lookup_event(rom, 0x2495), 0x123456)

    def test_past_soul_of_chaos_table(self):
        rom = Rom(bytearray(0x8000))
        with self.assertRaises(ValueError):
            lookup_event(rom, 0x2496)


def _disassemble_lines(script: bytes) -> list:
    rom = Rom(bytearray(0x100) + bytearray(script))
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        disassemble(rom, 0x100)
    return output.getvalue().splitlines()


class TestBattleCommands(unittest.TestCase):

    def test_event_battle(self):
        script = b'\x2b\x04\x05\xff' + b'\x00\x04\xff\xff'
        self.assertEqual(_disassemble_lines(script), ["event_battle 0x5", "end_event"])

    def test_battle_with_formation(self):
        script = b'\x98\x0c\xff\xff\x09\x01\x0e\x00\x00\x00\x00\x00' + b'\x00\x04\xff\xff'
        self.assertEqual(_disassemble_lines(script), ["battle 0x109 0xe", "end_event"])

    def test_battle_with_formation_and_address(self):
        script = (b'\x98\x0c\xff\xff\x09\x01\x0e\x00\x10\x01\x00\x08'
                  b'\x01\x04\xff\xff'
                  b'\x00\x04\xff\xff')
        self.assertEqual(_disassemble_lines(script),
                         ["battle 0x109 0xe .Label_1", "db 0x1 0x4 0xff 0xff", ".Label_1:", "end_event"])


if __name__ == '__main__':
    unittest.main()
