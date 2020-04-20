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

from doslib.rom import Rom
from doslib.textblock import TextBlock
from stream.outputstream import OutputStream


class EventTables(object):
    def __init__(self, rom: Rom):
        self._map_init = EventTable(rom, 0x7050, 0xD3, base_event_id=0x0)
        self._extra_events = EventTable(rom, 0x7900, 0x0a, base_event_id=0xFA0)
        self._main_events = EventTable(rom, 0x7788, 0x44, base_event_id=0x1388)
        self._dialog_events = EventTable(rom, 0x73A0, 0xef, base_event_id=0x1F40)

    def get_addr(self, event_id: int) -> int:
        if 0x0 <= event_id <= 0xD3:
            return self._map_init.get_addr(event_id)
        elif 0xFA0 <= event_id <= 0xFAA:
            return self._extra_events.get_addr(event_id)
        elif 0x1388 <= event_id <= 0x13CC:
            return self._main_events.get_addr(event_id)
        elif 0x1F40 <= event_id <= 0x202F:
            return self._dialog_events.get_addr(event_id)
        else:
            raise RuntimeError(f"Invalid event_id: {hex(event_id)}")

    def set_addr(self, event_id: int, value: int):
        if 0x0 <= event_id <= 0xD3:
            self._map_init.set_addr(event_id, value)
        elif 0xFA0 <= event_id <= 0xFAA:
            self._extra_events.set_addr(event_id, value)
        elif 0x1388 <= event_id <= 0x13CC:
            self._main_events.set_addr(event_id, value)
        elif 0x1F40 <= event_id <= 0x202F:
            self._dialog_events.set_addr(event_id, value)
        else:
            raise RuntimeError(f"Invalid event_id: {hex(event_id)}")

    def get_patches(self) -> dict:
        return {
            0x7050: self._map_init.get_lut(),
            0x7900: self._extra_events.get_lut(),
            0x7788: self._main_events.get_lut(),
            0x73A0: self._dialog_events.get_lut()
        }


class EventTable(object):
    def __init__(self, rom: Rom, table_offset: int, table_size: int, base_event_id=0):
        self._base_event_id = base_event_id
        self._lut = list(rom.get_lut(table_offset, table_size))

    def get_addr(self, event_id: int) -> int:
        return self._lut[event_id - self._base_event_id]

    def set_addr(self, event_id: int, value: int):
        self._lut[event_id - self._base_event_id] = value

    def get_lut(self) -> bytearray:
        stream = OutputStream()
        for addr in self._lut:
            stream.put_u32(addr)
        return stream.get_buffer()


class EventTextBlock(TextBlock):
    def __init__(self, rom: Rom):
        super().__init__(rom, 0x211770, 1280)

    def shrink(self):
        space = 0

        for index, estr in enumerate(self.strings):
            if index == 0:
                continue

            placeholder_text = hex(index).replace("0x", "")

            ascii_str = self[index]
            if ascii_str.startswith(placeholder_text) or ascii_str.startswith("NOT USED"):
                # Space saved!
                space += len(estr)

                # We set the string to None here, and then when the text block is written out, instead of writing
                # nothing, we'll update the pointer in the LUT to point to string 0, which will serve as a single
                # placeholder string.
                self.strings[index] = None
