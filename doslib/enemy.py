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
from stream.input import Input
from stream.output import Output


class EnemyStats(object):
    def __init__(self, stream: Input):
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
        self.unused_1 = stream.get_u8()
        self.elem_weakness = stream.get_u16()
        self.elem_resists = stream.get_u16()
        self.drop_type = stream.get_u8()
        self.drop_id = stream.get_u8()
        self.drop_chance = stream.get_u8()
        self.unused_2 = stream.get_u8()
        self.unused_3 = stream.get_u8()
        self.unused_4 = stream.get_u8()

    def write(self, stream: Output):
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
        stream.put_u8(self.unused_1)
        stream.put_u16(self.elem_weakness)
        stream.put_u16(self.elem_resists)
        stream.put_u8(self.drop_type)
        stream.put_u8(self.drop_id)
        stream.put_u8(self.drop_chance)
        stream.put_u8(self.unused_2)
        stream.put_u8(self.unused_3)
        stream.put_u8(self.unused_4)
