# -*- coding: utf-8 -*-
"""Data types in the Dawn of Souls ROM"""

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

#: -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#-
#:
#: Monster data types
#:
#: -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#- -#-

MonsterStatsTuple = namedtuple('MonsterStatsTuple',
                          ['exp_reward', 'gil_reward', 'hp', 'moral', 'evasion', 'defense', 'hit_count', 'accuracy',
                           'attack', 'agility', 'intelligence', 'crit_rate', 'status_attack_element',
                           'status_attack_ailment', 'family', 'magic_defense', 'elemental_weakness',
                           'elemental_resistances', 'item_drop_type', 'item_drop_id', 'item_drop_chance'])
MONSTER_STATS = "<HHHBxBBBBBBBBHBBBxHHBBBxxx"

EncounterDataTuple = namedtuple('EncounterDataTuple',
                           ['config', 'is_unrunnable', 'surprise_chance', 'group_1_id', 'group_1_min_count',
                            'group_1_max_count', 'group_2_id', 'group_2_min_count', 'group_2_max_count', 'group_3_id',
                            'group_3_min_count', 'group_3_max_count', 'group_4_id', 'group_4_min_count',
                            'group_4_max_count'])
ENCOUNTER_DATA = "<BBHBBBxBBBxBBBxBBBx"
