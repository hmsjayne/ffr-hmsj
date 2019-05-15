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
from doslib.gen.spells import SpellData
from doslib.rom import Rom
from doslib.textblock import TextBlock
from stream.outputstream import OutputStream


class Spells(object):
    def __init__(self, rom: Rom):
        # 130 Because:
        # 8 levels of magic, 8 spells per level (white + black) = 64 spells.
        # Spell name + help text for each = 64 x 2 = 128
        # Slot 0 is skipped = 128 + 2 (blank name + empty help) = 130
        self._name_help = TextBlock(rom, 0x1A1650, 130)

        spell_data_stream = rom.open_bytestream(0x1A1980, 0x740)
        self._spell_data = []
        for index in range(65):
            self._spell_data.append(SpellData(spell_data_stream))

    def write(self, rom: Rom) -> Rom:
        spell_stream = OutputStream()
        for spell in self._spell_data:
            spell.write(spell_stream)
        return rom.apply_patch(0x1A1980, spell_stream.get_buffer())

    def spell_name(self, index: int) -> str:
        return self._name_help[index * 2]

    def spell_help(self, index: int) -> str:
        return self._name_help[(index * 2) + 1]

    def spell_data(self, index: int) -> SpellData:
        return self._spell_data[index]

    def __getitem__(self, index):
        return self._spell_data[index]

    @staticmethod
    def index_for_level(school: chr, level: int, index: int) -> int:
        school_offset = 1 if school.lower() == "w" else 65
        return ((level - 1) * 4) + (index - 1) + school_offset
