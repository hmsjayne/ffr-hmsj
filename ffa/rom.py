# -*- coding: utf-8 -*-
"""Final Fantasy Advance: Dawn of Souls ROM

This module is intended be the 'base' of the module. The idea is that the "rom" contains the data structures
for each of the parts of the rom, which are themselves managed in sibling modules.

Some sibling modules will have dependencies upon one anther. For example, the monster module would likely
want to reference the strings module.

"""
from ffa.monster import unpack_monster_stats


def open_rom(path: str) -> tuple:
    """Opens a Final Fantasy Advance: Dawn of Souls ROM

    :param path: Path to the ROM to open
    :return: A byte tuple (immutable list) representing the ROM.
    """
    with open(path, "rb") as rom_file:
        rom_data = rom_file.read()
        return tuple(rom_data)


def load_monster_data(rom_data):
    MONSTER_DATA_BASE = 0x1DE044
    MONSTER_DATA_SIZE = 0x20

    monsters = list()
    for i in range(0, 195):
        start_addr = MONSTER_DATA_BASE + (MONSTER_DATA_SIZE * i)

        monster = unpack_monster_stats(rom_data[start_addr:start_addr + MONSTER_DATA_SIZE])
        monsters.append(monster)

    return tuple(monsters)
