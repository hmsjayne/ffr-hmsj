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


class Enemies(object):
    FLYING_MONSTER_IDS = [0x51, 0x52, 0x52, 0xA2, 0x3E, 0x3F, 0xBB]

    MINI_BOSS_IDS = [
        0xf,
        0x69,
        0x71,
        0x76
    ]

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

    def find_by_size(self, size):
        return (index for index in range(0, len(self.sizes)) if self.sizes[index] == size)

    @staticmethod
    def is_soc(id):
        # Soul of Chaos enemies start after Chaos (id=0x80)
        return id > 0x80

    @staticmethod
    def is_miniboss(id):
        # Soul of Chaos enemies start after Chaos (id=0x80)
        return id in Enemies.MINI_BOSS_IDS


class MonsterStats(MonsterStatsTuple):
    def scale_to(self, other):
        return other


class EncounterData(EncounterDataTuple):
    def is_soc(self):
        return self._is_group_soc(self.group_1_id) or self._is_group_soc(self.group_2_id) or \
               self._is_group_soc(self.group_3_id) or self._is_group_soc(self.group_4_id)

    def apply_shuffle(self, shuffled):
        id_1 = shuffled[self.group_1_id] if self.group_1_id in shuffled else self.group_1_id
        id_2 = shuffled[self.group_2_id] if self.group_2_id in shuffled else self.group_2_id
        id_3 = shuffled[self.group_3_id] if self.group_3_id in shuffled else self.group_3_id
        id_4 = shuffled[self.group_4_id] if self.group_4_id in shuffled else self.group_4_id

        new_config = self.config
        if self.config == 0x0 or self.config == 0x5:
            types = self._enemy_type(id_1) | self._enemy_type(id_2) | self._enemy_type(id_3) | self._enemy_type(id_4)
            if types == 0x1 or types == 0x2:
                # Either all land or all flying
                new_config = 0x0
            else:
                # Combo of flying + ground
                new_config = 0x5

        return self._replace(config=new_config,
                             group_1_id=id_1,
                             group_2_id=id_2,
                             group_3_id=id_3,
                             group_4_id=id_4)

    @staticmethod
    def _enemy_type(id):
        if id == 0xff:
            return 0
        elif id in Enemies.FLYING_MONSTER_IDS:
            return 2
        else:
            return 1

    @staticmethod
    def _is_group_soc(id):
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
