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
from collections import namedtuple

from doslib.dos_utils import load_tsv, decode_permission_string
from doslib.rom import Rom
from doslib.spell import SpellData
from doslib.textblock import TextBlock
from stream.outputstream import OutputStream

SpellExtraData = namedtuple("SpellExtraData",
                            ["spell_index", "name", "school", "permissions", "usage", "target", "power", "elements",
                             "type",
                             "graphic_index", "accuracy", "level", "mp_cost", "price", "grade"])


class Spells(object):
    def __init__(self, rom: Rom):
        # 130 Because:
        # 8 levels of magic, 8 spells per level (white + black) = 64 spells.
        # Spell name + help text for each = 64 x 2 = 128
        # Slot 0 is skipped = 128 + 2 (blank name + empty help) = 130
        self._name_help = TextBlock(rom, 0x1A1650, 130)
        self.spell_data = []
        self.permissions = []
        self.shuffled_permission = []

        spell_data_stream = rom.open_bytestream(0x1A1980, 0x740)
        for index in range(65):
            self.spell_data.append(SpellData(spell_data_stream))
            self.shuffled_permission.append(0)

        for spell_data in load_tsv("data/SpellData.tsv"):
            extra = SpellExtraData(*spell_data)
            self.shuffled_permission[extra.spell_index] = decode_permission_string(extra.permissions)

            self.spell_data[extra.spell_index].name = extra.name
            self.spell_data[extra.spell_index].school = extra.school
            self.spell_data[extra.spell_index].grade = extra.grade
            self.spell_data[extra.spell_index].spell_index = extra.spell_index

        permissions_stream = rom.open_bytestream(0x1A20C0, 0x82)
        while not permissions_stream.is_eos():
            self.permissions.append(permissions_stream.get_u16())

    def get_patches(self) -> dict:
        spell_stream = OutputStream()
        for spell in self.spell_data:
            spell.write(spell_stream)

        permissions_stream = OutputStream()
        for permission in self.permissions:
            permissions_stream.put_u16(permission)

        return {
            0x1A1980: spell_stream.get_buffer(),
            0x1A20C0: permissions_stream.get_buffer()
        }

    def spell_name(self, index: int) -> str:
        return self._name_help[index * 2]

    def spell_help(self, index: int) -> str:
        return self._name_help[(index * 2) + 1]

    def spell_data(self, index: int) -> SpellData:
        return self.spell_data[index]

    def __getitem__(self, index):
        return self.spell_data[index]

    @staticmethod
    def index_for_level(school: chr, level: int, index: int) -> int:
        school_offset = 1 if school.lower() == "w" else 65
        return ((level - 1) * 4) + (index - 1) + school_offset
