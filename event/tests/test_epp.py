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

import unittest

from event.epp import pparse


class TestEpp(unittest.TestCase):

    def test_basic_input(self):
        code = """
        jump .End
        .Loop:
        jump .Loop
        .End:
        """
        pp_output = pparse(code)
        self.assertEqual(_block_strip(pp_output), _block_strip(code))

    def test_basic_if(self):
        in_code = """
        #ifdef MISSING
        jump .End
        .Loop:
        jump .Loop
        #endif
        .End:
        """
        out_code = """
        .End:
        """
        pp_output = pparse(in_code)
        self.assertEqual(_block_strip(pp_output), _block_strip(out_code))

    def test_basic_if_else(self):
        in_code = """
        #ifdef MISSING
        jump .End
        .Loop:
        jump .Loop
        #else
        set_flag %flag 0x1
        #endif
        .End:
        """
        out_code = """
        set_flag %flag 0x1
        .End:
        """
        pp_output = pparse(in_code)
        self.assertEqual(_block_strip(pp_output), _block_strip(out_code))

    def test_if_no_end(self):
        in_code = """
        #ifdef MISSING
        jump .End
        .Loop:
        jump .Loop
        .EndIsMissing:
        """
        with self.assertRaises(RuntimeError):
            pp_output = pparse(in_code)

    def test_if_multi_else(self):
        in_code = """
        #ifdef MISSING
        jump .End
        #else
        .Loop:
        #else
        jump .Loop
        .EndIsMissing:
        #endif
        end_event
        """
        with self.assertRaises(RuntimeError):
            pp_output = pparse(in_code)

    def test_basic_ifndef(self):
        in_code = """
        #ifndef MISSING
        jump .End
        .Loop:
        jump .Loop
        #endif
        .End:
        """
        out_code = """
        jump .End
        .Loop:
        jump .Loop
        .End:
        """
        pp_output = pparse(in_code)
        self.assertEqual(_block_strip(pp_output), _block_strip(out_code))

    def test_nested_ifs(self):
        in_code = """
        #define TEST_1 0x1
        
        #ifndef TEST_1
        ; This is missing from the output
        #else
        ; This is included
        #ifdef MISSING
        ; This is not included
        #else
        ; This is
        #endif
        #endif
        """
        out_code = """
        ; This is included
        ; This is
        """
        pp_output = pparse(in_code)
        self.assertEqual(_block_strip(pp_output), _block_strip(out_code))

    def test_define(self):
        in_code = """
        #define TEST_DEF 0x1
        
        ; The output of this is TEST_DEF
        """
        out_code = """
        ; The output of this is 0x1
        """
        pp_output = pparse(in_code)
        self.assertEqual(_block_strip(pp_output), _block_strip(out_code))

    def test_if_multi_end(self):
        in_code = """
        #ifdef MISSING
        jump .End
        #endif
        .Loop:
        jump .Loop
        .EndIsMissing:
        #endif
        end_event
        """
        with self.assertRaises(RuntimeError):
            pp_output = pparse(in_code)

def _block_strip(text: str) -> str:
    out = []
    for line in text.split():
        out.append(line.strip())
    return "\n".join(out)
