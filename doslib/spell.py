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
#  Generated on 2020-12-22 22:49

from stream.inputstream import InputStream
from stream.outputstream import OutputStream


class SpellData(object):
    def __init__(self, stream: InputStream = None):
        if stream is None:
            self.usage = 0
            self.target = 0
            self.power = 0
            self.elements = 0
            self.type = 0
            self.graphic_index = 0
            self.accuracy = 0
            self.level = 0
            self.mp_cost = 0
            self.price = 0
            self.spell_index = 0
            self.name = None
            self.school = None
            self.grade = None

        else:
            self.usage = stream.get_u8()
            self.target = stream.get_u8()
            self.power = stream.get_u16()
            self.elements = stream.get_u16()
            self.type = stream.get_u8()
            self.graphic_index = stream.get_u8()
            self.accuracy = stream.get_u8()
            self.level = stream.get_u8()
            self.mp_cost = stream.get_u16()
            self.price = stream.get_u32()
            self.spell_index = 0
            self.name = None
            self.school = None
            self.grade = None

    def write(self, stream: OutputStream):
        stream.put_u8(self.usage)
        stream.put_u8(self.target)
        stream.put_u16(self.power)
        stream.put_u16(self.elements)
        stream.put_u8(self.type)
        stream.put_u8(self.graphic_index)
        stream.put_u8(self.accuracy)
        stream.put_u8(self.level)
        stream.put_u16(self.mp_cost)
        stream.put_u32(self.price)


