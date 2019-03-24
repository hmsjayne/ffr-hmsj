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

from ffa.enemies import unpack_encounter_data, Enemies, pack_encounter_data, unpack_enemy_stats, pack_enemy_stats
from ffa.ffstring import FFString


class Rom(object):
    def __init__(self, path: str = None, data: bytearray = None):
        if path is not None and data is None:
            with open(path, "rb") as rom_file:
                self.rom_data = rom_file.read()
        elif path is None and data is not None:
            self.rom_data = data
        else:
            raise RuntimeError("Pass only the path of the ROM to load")

        self.encounters = self._load_encounter_data()
        self.enemies = Enemies(self)

        self.event_strings = TextBlock(self, 0x211770, 1000)

    def find_string(self, offset):
        end_offset = offset
        while self.rom_data[end_offset] != 0x0:
            end_offset += 1
        return self.rom_data[offset:end_offset + 1]

    def read_pointer_as_offset(self, pointer_offset):
        pointer_bytes = self.rom_data[pointer_offset:pointer_offset + 4]
        pointer = int.from_bytes(pointer_bytes, byteorder="little", signed=False)
        return pointer - 0x8000000

    def apply_patches(self, patches):
        """Applies a set of patches to a the rom.

        :param patches: Patches to apply as a dictionary. Keys are offsets, values are patch data.
        :return: A patched version of the rom.
        """
        new_data = bytearray()

        working_offset = 0
        for offset in sorted(patches.keys()):
            if working_offset > offset:
                raise RuntimeError(f"Could not apply patch to {offset}; already at {working_offset}!")

            # Check if there's missing data between our working position and the next patch
            if working_offset < offset:
                new_data.extend(self.rom_data[working_offset:offset])

            # Now that we're caught up, plop the patch in, and update the working offset.
            patch = patches[offset]
            new_data.extend(patch)
            working_offset = offset + len(patch)

        # Now that the patches are applied, add whatever is left of the file.
        new_data.extend(self.rom_data[working_offset:])

        new_rom = Rom(data=new_data)
        return new_rom

    def with_new_encounters(self, encounters):
        ENCOUNTER_DATA_BASE = 0x2288B4
        ENCOUNTER_DATA_SIZE = 0x14
        ENCOUNTER_DATA_COUNT = 0x171

        new_data = bytearray()
        new_data.extend(self.rom_data[0:ENCOUNTER_DATA_BASE])
        new_data.extend(pack_encounter_data(encounters))
        new_data.extend(self.rom_data[ENCOUNTER_DATA_BASE + (ENCOUNTER_DATA_SIZE * ENCOUNTER_DATA_COUNT):])

        new_rom = Rom(data=new_data)
        return new_rom

    def with_new_enemies(self, enemies):
        ENEMY_DATA_BASE = 0x1DE044
        ENEMY_DATA_SIZE = 0x20
        ENEMY_DATA_COUNT = 0xC2

        new_data = bytearray()
        new_data.extend(self.rom_data[0:ENEMY_DATA_BASE])
        new_data.extend(pack_enemy_stats(enemies))
        new_data.extend(self.rom_data[ENEMY_DATA_BASE + (ENEMY_DATA_SIZE * ENEMY_DATA_COUNT):])

        new_rom = Rom(data=new_data)
        return new_rom

    def write(self, path):
        with open(path, "wb") as rom_file:
            rom_file.write(self.rom_data)
            rom_file.close()

    def __getitem__(self, index):
        return self.rom_data[index]

    def __setitem__(self, index, value):
        raise RuntimeError("Rom objects are immutable.")

    def size(self):
        return len(self.rom_data)

    def _load_encounter_data(self):
        ENCOUNTER_DATA_BASE = 0x2288B4
        ENCOUNTER_DATA_SIZE = 0x14
        ENCOUNTER_DATA_COUNT = 0x171

        encounters = list()
        for i in range(0, ENCOUNTER_DATA_COUNT):
            start_addr = ENCOUNTER_DATA_BASE + (ENCOUNTER_DATA_SIZE * i)

            encounter = unpack_encounter_data(self.rom_data[start_addr:start_addr + ENCOUNTER_DATA_SIZE])
            encounters.append(encounter)

        return tuple(encounters)


class TextBlock(object):
    def __init__(self, rom: Rom, lut_addr: int, lut_size):
        self._strings = list()
        for i in range(0, lut_size):
            start = lut_addr + (i * 4)
            offset = rom.read_pointer_as_offset(start)
            string_data = FFString(offset, rom.find_string(offset))
            self._strings.append(string_data)

    def __getitem__(self, index):
        return self._strings[index]
