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
from stream.inputstream import InputStream
from stream.outputstream import OutputStream


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


class Event(object):
    def __init__(self, stream: InputStream):
        self.commands = []

        last_cmd = -1
        while last_cmd != 0:
            cmd = [stream.get_u8()]
            cmd_len = stream.get_u8()
            cmd.append(cmd_len)

            # 2 Bytes already read -- the command, and length
            for params in range(cmd_len - 2):
                cmd.append(stream.get_u8())

            self.commands.append(EventCommand(cmd))
            last_cmd = cmd[0]

    def write(self, stream: OutputStream):
        for cmd in self.commands:
            for data in cmd:
                stream.put_u8(data)


class EventCommand(list):
    def cmd(self) -> int:
        return self[0]

    def size(self) -> int:
        return self[1]

    def get_u16(self, index: int) -> int:
        if index % 2 == 0:
            return self[index] | (self[index + 1] << 8)
        raise RuntimeError(f"Event parameters are always word aligned")

    def get_u32(self, index: int) -> int:
        if index % 4 == 0:
            return self[index] | (self[index + 1] << 8) | (self[index + 2] << 16) | (self[index + 3] << 24)
        raise RuntimeError(f"Event parameters are always word aligned")

    def put_u16(self, index: int, value: int):
        if index % 2 == 0:
            self[index] = value & 0xff
            self[index + 1] = (value >> 8) & 0xff
        else:
            raise RuntimeError(f"Event parameters are always word aligned")

    def put_u32(self, index: int, value: int):
        if index % 4 == 0:
            self[index] = value & 0xff
            self[index + 1] = (value >> 8) & 0xff
            self[index + 2] = (value >> 16) & 0xff
            self[index + 3] = (value >> 24) & 0xff
        else:
            raise RuntimeError(f"Event parameters are always word aligned")

    def __str__(self) -> str:
        return "[" + ",".join(format(x, "02x") for x in self) + "]"
