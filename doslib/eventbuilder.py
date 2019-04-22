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

from __future__ import annotations

from stream.output import Output


class EventBuilder(object):
    def __init__(self):
        self._labels = {}
        self._flags = {}
        self._stream = Output()

    def add_label(self, label: str, addr=-1) -> EventBuilder:
        if label not in self._labels:
            self._labels[label] = addr
        return self

    def add_flag(self, name: str, flag_id: int) -> EventBuilder:
        if name not in self._flags:
            self._flags[name] = flag_id
        return self

    def set_flag(self, flag_name: str, condition: int) -> EventBuilder:
        if flag_name not in self._flags:
            raise RuntimeError(f"Undefined flag: {flag_name}")

        self._stream.put_u8(0x2d)
        self._stream.put_u8(0x4)
        self._stream.put_u8(self._flags[flag_name])
        self._stream.put_u8(condition)
        return self

    def jump_to(self, label: str) -> EventBuilder:
        if label not in self._labels:
            raise RuntimeError(f"Undefined label: {label}")

        addr = self._labels[label]
        if addr == -1:
            raise RuntimeError(f"Address for {label} was not set")

        self._stream.put_u8(0x0c)
        self._stream.put_u8(0x8)
        self._stream.put_u16(0xffff)
        self._stream.put_u32(addr)
        return self

    def check_flag_and_jump(self, flag_name: str, condition: int, label: str) -> EventBuilder:
        if flag_name not in self._flags:
            raise RuntimeError(f"Undefined flag: {flag_name}")
        if label not in self._labels:
            raise RuntimeError(f"Undefined label: {label}")

        addr = self._labels[label]
        if addr == -1:
            raise RuntimeError(f"Address for {label} was not set")

        self._stream.put_u8(0x2d)
        self._stream.put_u8(0x8)
        self._stream.put_u8(self._flags[flag_name])
        self._stream.put_u8(condition)
        self._stream.put_u32(addr)
        return self

    def set_event_on_npc(self, npc_id: int, event_id: int) -> EventBuilder:
        self._stream.put_u8(0x30)
        self._stream.put_u8(0x8)
        self._stream.put_u8(0x1)
        self._stream.put_u8(npc_id)
        self._stream.put_u16(event_id)
        self._stream.put_u16(0xffff)
        return self

    def event_end(self) -> EventBuilder:
        self._stream.put_u8(0x0)
        self._stream.put_u8(0x4)
        self._stream.put_u16(0xffff)
        return self

    def nop(self) -> EventBuilder:
        self._stream.put_u8(0x1)
        self._stream.put_u8(0x4)
        self._stream.put_u16(0xffff)
        return self

    def get_event(self) -> bytearray:
        return self._stream.get_buffer()

    def set_npc_pose(self, npc_id: int, direction: int) -> EventBuilder:
        self._stream.put_u8(0x21)
        self._stream.put_u8(0x4)
        self._stream.put_u8(npc_id)
        self._stream.put_u8(direction)
        return self

    def wait_frames(self, number_of_frames: int) -> EventBuilder:
        self._stream.put_u8(0x9)
        self._stream.put_u8(0x4)
        self._stream.put_u16(number_of_frames)
        return self
