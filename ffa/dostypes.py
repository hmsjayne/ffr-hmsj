# -*- coding: utf-8 -*-
"""Data types in the Dawn of Souls ROM"""

from collections import namedtuple

#: -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#-
#:
#: Monster data types
#:
#: -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#-

MonsterStats = namedtuple('MonsterStats', 'exp_reward gil_reward hp moral evasion defense '
                                          'hit_count accuracy attack agility intelligence crit_rate '
                                          'status_attack_element status_attack_ailment family magic_defense '
                                          'elemental_weakness elemental_resistances '
                                          'item_drop_type item_drop_id item_drop_chance')
MONSTER_STATS = "<HHHBxBBBBBBBBHBBBxHHBBBxxx"
