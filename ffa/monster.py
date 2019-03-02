# -*- coding: utf-8 -*-
"""Representation of a monster"""

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
