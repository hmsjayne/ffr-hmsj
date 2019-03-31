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

from stream.output import Output


class EventBuilder(object):
    def __init__(self):
        self._labels = {}
        self._flags = {}
        self._stream = Output()

    def add_label(self, label: str, addr=-1):
        if label not in self._labels:
            self._labels[label] = addr

    def add_flag(self, name: str, flag_id: int):
        if name not in self._flags:
            self._flags[name] = flag_id

    def set_flag(self, flag_name: str, condition: int):
        if flag_name not in self._flags:
            raise RuntimeError(f"Undefined flag: {flag_name}")

        self._stream.put_u8(0x2d)
        self._stream.put_u8(0x4)
        self._stream.put_u8(self._flags[flag_name])
        self._stream.put_u8(condition)

    def jump_to(self, label: str):
        if label not in self._labels:
            raise RuntimeError(f"Undefined label: {label}")

        addr = self._labels[label]
        if addr == -1:
            raise RuntimeError(f"Address for {label} was not set")

        self._stream.put_u8(0x0c)
        self._stream.put_u8(0x8)
        self._stream.put_u16(0xffff)
        self._stream.put_u32(addr)

    def set_event_on_npc(self, npc_id: int, event_id: int):
        self._stream.put_u8(0x30)
        self._stream.put_u8(0x8)
        self._stream.put_u8(0x1)
        self._stream.put_u8(npc_id)
        self._stream.put_u16(event_id)
        self._stream.put_u16(0xffff)

    def event_end(self):
        self._stream.put_u8(0x0)
        self._stream.put_u8(0x4)
        self._stream.put_u16(0xffff)

    def get_event(self):
        return self._stream.get_buffer()
