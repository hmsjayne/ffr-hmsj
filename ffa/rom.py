# -*- coding: utf-8 -*-
"""Final Fantasy Advance: Dawn of Souls ROM

This module is intended be the 'base' of the module. The idea is that the "rom" contains the data structures
for each of the parts of the rom, which are themselves managed in sibling modules.

Some sibling modules will have dependencies upon one anther. For example, the monster module would likely
want to reference the strings module.

"""
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

from ffa.monster import unpack_monster_stats
from ffa.text import text_to_ascii


def open_rom(path: str) -> tuple:
    """Opens a Final Fantasy Advance: Dawn of Souls ROM

    :param path: Path to the ROM to open
    :return: A byte tuple (immutable list) representing the ROM.
    """
    with open(path, "rb") as rom_file:
        rom_data = rom_file.read()
        return tuple(rom_data)


def write_rom(path: str, data: tuple):
    with open(path, "wb") as rom_file:
        rom_file.write(bytearray(data))
        rom_file.close()


def load_monster_data(rom_data):
    MONSTER_DATA_BASE = 0x1DE044
    MONSTER_DATA_SIZE = 0x20

    monsters = list()
    for i in range(0, 195):
        start_addr = MONSTER_DATA_BASE + (MONSTER_DATA_SIZE * i)

        monster = unpack_monster_stats(rom_data[start_addr:start_addr + MONSTER_DATA_SIZE])
        monsters.append(monster)

    return tuple(monsters)

def load_monster_names(rom_data):
    MONSTER_NAME_PTRS = 0x1DDD38

    names = list()
    for i in range(0, 195):
        start = MONSTER_NAME_PTRS + (i * 4)
        pointer = unpack("<I", bytearray(rom_data[start:start + 4]))[0]
        offset = pointer - 0x8000000
        names.append(text_to_ascii(rom_data[offset:offset + 0x100]))
    return tuple(names)

