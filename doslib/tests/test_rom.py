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

from doslib.rom import Rom
from stream.outputstream import OutputStream


class TestRom(unittest.TestCase):

    def setUp(self):
        self.rom = Rom(data=bytearray([
            # String (0x0)
            0x82, 0x66, 0x82, 0x8f, 0x82, 0x82, 0x82, 0x8c, 0x82, 0x89, 0x82, 0x8e, 0x00, 0x00, 0x00, 0x00,
            # LUT (0x10)
            0x34, 0x12, 0x00, 0x08, 0x78, 0x56, 0x00, 0x08, 0xbc, 0x9a, 0x00, 0x08, 0xf0, 0xde, 0x00, 0x08
        ]))

    def test_open_bytestream(self):
        stream = self.rom.open_bytestream(0x0, 0x4)
        self.assertEqual(stream.size(), 4)
        self.assertEqual(stream.get_u16(), 0x6682)

    def test_open_bytestream_out_of_bounds(self):
        with self.assertRaises(RuntimeError):
            stream = self.rom.open_bytestream(0x100, 0x4)

    def test_get_lut(self):
        lut = self.rom.get_lut(0x10, 4)
        self.assertEqual(len(lut), 4)

        addressses = [
            0x8001234,
            0x8005678,
            0x8009abc,
            0x800def0,
        ]
        for index, address in enumerate(lut):
            self.assertEqual(address, addressses[index])

    def test_get_lut_misaligned(self):
        with self.assertRaises(RuntimeError):
            lut = self.rom.get_lut(0x12, 2)

    def test_get_string(self):
        a_str = self.rom.get_string(0x0)
        self.assertEqual(len(a_str), 0xd)

    def test_patch(self):
        patch = OutputStream()
        patch.put_u32(0x12345678)
        patched = self.rom.apply_patch(0x0, patch.get_buffer())
        confirm = patched.open_bytestream(0x0, 0x4)
        self.assertEqual(confirm.get_u32(), 0x12345678)

    def test_patches(self):
        patch = OutputStream()
        patch.put_u32(0x12345678)
        patched = self.rom.apply_patches({
            0x0: patch.get_buffer(),
            0x10: patch.get_buffer()
        })
        confirm = patched.open_bytestream(0x0, 0x4)
        self.assertEqual(confirm.get_u32(), 0x12345678)

        confirm = patched.open_bytestream(0x10, 0x4)
        self.assertEqual(confirm.get_u32(), 0x12345678)

    def test_overlap_patch(self):
        patch = OutputStream()
        patch.put_u32(0x12345678)
        patch.put_u32(0x12345678)
        with self.assertRaises(RuntimeError):
            patched = self.rom.apply_patches({
                0x0: patch.get_buffer(),
                0x4: patch.get_buffer()
            })
            self.assertNotEqual(patched, patched)


if __name__ == '__main__':
    unittest.main()
