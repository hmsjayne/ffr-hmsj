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

from event import easm
import unittest


class Testeasm(unittest.TestCase):

    def test_simple_gen_no_params(self):
        op_format = [0x0, 0x4, 0xff, 0xff]
        parameters = []
        output = easm.simple_gen(op_format, parameters)
        self.assertEqual(output, [0x0, 0x4, 0xff, 0xff])

    def test_simple_gen_params(self):
        op_format = [0xc, 0x8, 0xff, 0xff, "$0"]
        parameters = [".EventEnd"]
        output = easm.simple_gen(op_format, parameters)
        self.assertEqual(output, [0xc, 0x8, 0xff, 0xff, ".EventEnd"])

    def test_simple_gen_with_size_byte(self):
        op_format = [0xc, 0x8, 0xff, 0xff, "$(x:0)"]
        parameters = [".EventEnd"]
        output = easm.simple_gen(op_format, parameters)
        self.assertEqual(output, [0xc, 0x8, 0xff, 0xff, ".EventEnd"])

    def test_simple_gen_with_size_u16(self):
        op_format = [0x11, 0x8, "$0", 0xff, "$(u:1)", 0xff, 0xff]
        parameters = [0x0, 0x1234]
        output = easm.simple_gen(op_format, parameters)
        self.assertEqual(output, [0x11, 0x8, 0x0, 0xff, 0x34, 0x12, 0xff, 0xff])

    def test_simple_gen_with_size_u32(self):
        op_format = [0x11, 0x8, "$0", 0xff, "$(U:1)"]
        parameters = [0x0, 0x12345678]
        output = easm.simple_gen(op_format, parameters)
        self.assertEqual(output, [0x11, 0x8, 0x0, 0xff, 0x78, 0x56, 0x34, 0x12])

    def test_simple_gen_with_size_invalid(self):
        op_format = [0x11, 0x8, "$0", 0xff, "$(w:1)", 0xff, 0xff]
        parameters = [0x0, 0x1234]
        with self.assertRaises(RuntimeError):
            output = easm.simple_gen(op_format, parameters)
            # Fail if it doesn't raise
            self.assertNotEqual(output, output)


if __name__ == '__main__':
    unittest.main()
