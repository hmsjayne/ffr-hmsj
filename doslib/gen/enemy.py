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
#
#  This file is generated by build_types.py from datatype.def.
#
#  DO NOT EDIT THIS FILE DIRECTLY. Update "datatype.def" and rerun "build_types.py"
#
#  Generated on 2019-05-12 08:53

from stream.inputstream import InputStream
from stream.outputstream import OutputStream


class EnemyStats(object):
    def __init__(self, stream: InputStream = None):
        if stream is None:
            self.exp_reward = 0
            self.gil_reward = 0
            self.max_hp = 0
            self.morale = 0
            self.unused_ai = 0
            self.evasion = 0
            self.pdef = 0
            self.hit_count = 0
            self.acc = 0
            self.atk = 0
            self.agi = 0
            self.intel = 0
            self.crit_rate = 0
            self.status_atk_elem = 0
            self.status_atk_ailment = 0
            self.family = 0
            self.mdef = 0
            self.unused = 0
            self.elem_weakness = 0
            self.elem_resists = 0
            self.drop_type = 0
            self.drop_id = 0
            self.drop_chance = 0
            self.padding = []

        else:
            self.exp_reward = stream.get_u16()
            self.gil_reward = stream.get_u16()
            self.max_hp = stream.get_u16()
            self.morale = stream.get_u8()
            self.unused_ai = stream.get_u8()
            self.evasion = stream.get_u8()
            self.pdef = stream.get_u8()
            self.hit_count = stream.get_u8()
            self.acc = stream.get_u8()
            self.atk = stream.get_u8()
            self.agi = stream.get_u8()
            self.intel = stream.get_u8()
            self.crit_rate = stream.get_u8()
            self.status_atk_elem = stream.get_u16()
            self.status_atk_ailment = stream.get_u8()
            self.family = stream.get_u8()
            self.mdef = stream.get_u8()
            self.unused = stream.get_u8()
            self.elem_weakness = stream.get_u16()
            self.elem_resists = stream.get_u16()
            self.drop_type = stream.get_u8()
            self.drop_id = stream.get_u8()
            self.drop_chance = stream.get_u8()
            self.padding = []
            for index in range(3):
                self.padding.append(stream.get_u8())

    def write(self, stream: OutputStream):
        stream.put_u16(self.exp_reward)
        stream.put_u16(self.gil_reward)
        stream.put_u16(self.max_hp)
        stream.put_u8(self.morale)
        stream.put_u8(self.unused_ai)
        stream.put_u8(self.evasion)
        stream.put_u8(self.pdef)
        stream.put_u8(self.hit_count)
        stream.put_u8(self.acc)
        stream.put_u8(self.atk)
        stream.put_u8(self.agi)
        stream.put_u8(self.intel)
        stream.put_u8(self.crit_rate)
        stream.put_u16(self.status_atk_elem)
        stream.put_u8(self.status_atk_ailment)
        stream.put_u8(self.family)
        stream.put_u8(self.mdef)
        stream.put_u8(self.unused)
        stream.put_u16(self.elem_weakness)
        stream.put_u16(self.elem_resists)
        stream.put_u8(self.drop_type)
        stream.put_u8(self.drop_id)
        stream.put_u8(self.drop_chance)
        for data in self.padding:
            stream.put_u8(data)


class Encounter(object):
    def __init__(self, stream: InputStream = None):
        if stream is None:
            self.config = 0
            self.unrunnable = 0
            self.surprise_chance = 0
            self.groups = []

        else:
            self.config = stream.get_u8()
            self.unrunnable = stream.get_u8()
            self.surprise_chance = stream.get_u16()
            self.groups = []
            for index in range(4):
                self.groups.append(EncounterGroup(stream))

    def write(self, stream: OutputStream):
        stream.put_u8(self.config)
        stream.put_u8(self.unrunnable)
        stream.put_u16(self.surprise_chance)
        for data in self.groups:
            data.write(stream)


class EncounterGroup(object):
    def __init__(self, stream: InputStream = None):
        if stream is None:
            self.enemy_id = 0
            self.min_count = 0
            self.max_count = 0
            self.unused = 0

        else:
            self.enemy_id = stream.get_u8()
            self.min_count = stream.get_u8()
            self.max_count = stream.get_u8()
            self.unused = stream.get_u8()

    def write(self, stream: OutputStream):
        stream.put_u8(self.enemy_id)
        stream.put_u8(self.min_count)
        stream.put_u8(self.max_count)
        stream.put_u8(self.unused)


