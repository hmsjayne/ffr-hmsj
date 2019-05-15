#  Copyright 2019 Nicole Borrelli
#
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

"""Tests for the easm module. """

import unittest

from event.easm import *


class TestEasm(unittest.TestCase):

    def test_simple_jump(self):
        code = """
        jump .End
        .Loop:
        jump .Loop
        .End:
        """
        bytecode = parse(code, base_addr=0x8000000)
        self.assertEqual(bytecode, b'\x0c\x08\xff\xff\x10\x00\x00\x08\x0c\x08\xff\xff\x08\x00\x00\x08')

    def test_symbol_def(self):
        code = """
        %have_mystic_key 0x9
        check_flag %have_mystic_key jz .NoKey
        nop ; Have the mystic key
        jump .End
        .NoKey:
        nop ; Don't have the mystic key
        .End:
        """
        bytecode = parse(code, base_addr=0x8000000)
        self.assertEqual(bytecode, b'-\x08\t\x02\x14\x00\x00\x08\x01\x04\xff\xff\x0c\x08\xff\xff'
                                   b'\x18\x00\x00\x08\x01\x04\xff\xff')

    def test_jump_to_undefined(self):
        code = """
        jump .End
        .Loop:
        jump .Loop
        .EndIsMissing:
        """
        with self.assertRaises(UndefinedLabel):
            bytecode = parse(code, base_addr=0x8000000)
            self.assertNotEqual(bytecode, bytecode)

    def test_undefined_symbol(self):
        code = """
        check_flag %unknown jz .Elsewhere
        nop
        .Elsewhere:
        end_event
        """
        with self.assertRaises(SymbolNotDefinedError):
            bytecode = parse(code, base_addr=0x8000000)
            self.assertNotEqual(bytecode, bytecode)

    def test_duplicate(self):
        code = """
        %dup_flag 0x5
        check_flag %dup_flag jz .Elsewhere

        %dup_flag 0x5
        nop

        .Elsewhere:
        end_event
        """
        with self.assertRaises(DuplicateSymbolError):
            bytecode = parse(code, base_addr=0x8000000)
            self.assertNotEqual(bytecode, bytecode)


if __name__ == '__main__':
    unittest.main()
