# -*- coding: utf-8 -*-
"""Text manipulation methods"""

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
from struct import unpack

TEXT_TABLE = {}


def load_text_table():
    global TEXT_TABLE
    with open("data/text_table.txt", 'r') as text_table:
        for line in text_table:
            items = line.split("=")
            TEXT_TABLE[int(items[0], 16)] = items[1].rstrip()


def text_to_ascii(text):
    global TEXT_TABLE
    if 0x00 not in TEXT_TABLE:
        load_text_table()

    index = 0
    working = ""
    while text[index] != 0x00:
        if text[index] > 0x80:
            char_code = unpack(">H", bytearray(text[index:index+2]))[0]
            working = working + TEXT_TABLE[char_code]
            index = index + 1
        elif text[index] == 0x25:
            if text[index + 1] in [30, 31, 64, 73]:
                char_code = unpack(">H", bytearray(text[index:index + 2]))[0]
                working = working + TEXT_TABLE[char_code]
                index = index + 1
            elif text[index + 1] == 0x32:
                if text[index + 2] == 0x64:
                    char_code = 0x253264
                    working = working + TEXT_TABLE[char_code]
                    index = index + 2
                else:
                    char_code = 0x2532
                    working = working + TEXT_TABLE[char_code]
                    index = index + 1
        elif text[index] in [0x0a, 0x2d, 0x2e]:
            working = working + TEXT_TABLE[text[index]]
        else:
            raise RuntimeError(f"Unknown code encountered in string: {hex(text[index])}")

        index = index + 1
    return working
