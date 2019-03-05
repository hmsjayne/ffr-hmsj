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

from ffa.dostypes import MonsterStats, MONSTER_STATS


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
