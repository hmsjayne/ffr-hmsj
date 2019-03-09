# -*- coding: utf-8 -*-
"""Representation of a monster"""

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

from struct import unpack, pack

from ffa.dostypes import MONSTER_STATS, ENCOUNTER_DATA, MonsterStatsTuple, EncounterDataTuple
from ffa.text import text_to_ascii

FLYING_MONSTER_IDS = [0x51, 0x52, 0x52, 0xA2, 0x3E, 0x3F, 0xBB]


class Enemies(object):
    def __init__(self, rom):
        MONSTER_DATA_BASE = 0x223644
        self.sizes = rom[MONSTER_DATA_BASE:(MONSTER_DATA_BASE + 195)]

        MONSTER_NAME_PTRS = 0x1DDD38
        names = list()
        for i in range(0, 195):
            start = MONSTER_NAME_PTRS + (i * 4)
            offset = rom.read_pointer_as_offset(start)
            string_data = rom.find_string(offset)
            names.append(text_to_ascii(string_data))
        self.names = tuple(names)

    def find_by_size(self, size, withsoc=False):
        end = len(self.sizes) if withsoc else 0x80
        return (index for index in range(0, end) if self.sizes[index] == size)

class MonsterStats(MonsterStatsTuple):
    def scaleTo(self, other):
        return other


class EncounterData(EncounterDataTuple):
    def is_soc(self):
        return self._is_group_soc(self.group_1_id) or self._is_group_soc(self.group_2_id) or \
               self._is_group_soc(self.group_3_id) or self._is_group_soc(self.group_4_id)

    def _is_group_soc(self, id):
        if id == 0xff or id < 0x80:
            return False
        else:
            return True


def unpack_monster_stats(rom_data):
    """Unpacks monster stat data from ROM data

    :param rom_data: ROM data for the monster to unpack as a tuple (32 bytes)
    :return: A [MonsterStats] namedtuple with the data unpacked.
    """
    return MonsterStats(*unpack(MONSTER_STATS, bytearray(rom_data)))


def pack_monster_stats(stats):
    """Packs monster stat namedtuple into a tuple to be restitched into a ROM file.

    :param stats: The updated monster stats.
    :return: Byte tuple of the namedtuple.
    """
    return pack(MONSTER_STATS, *stats)


def unpack_encounter_data(data):
    return EncounterData(*unpack(ENCOUNTER_DATA, bytearray(data)))


def pack_encounter_data(data):
    packed_data = []
    for element in data:
        packed_data.extend(pack(ENCOUNTER_DATA, *element))
    return packed_data
