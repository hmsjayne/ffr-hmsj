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
import struct

from doslib.bytestream import ByteStream


class Rom(object):
    def __init__(self, path: str = None, data: bytearray = None):
        if path is not None and data is None:
            with open(path, "rb") as rom_file:
                self.rom_data = rom_file.read()
        elif path is None and data is not None:
            self.rom_data = data
        else:
            raise RuntimeError("Pass only the path of the ROM to load")

    def open_bytestream(self, offset: int, size: int = -1):
        if 0 <= offset < len(self.rom_data):
            data = self.rom_data[offset:] if size < 0 else self.rom_data[offset:(offset + size)]
            return ByteStream(data)
        raise RuntimeError(f"Index out of bounds {hex(offset)} vs {len(self.rom_data)}")

    def get_lut(self, offset: int, count: int):
        if len(self.rom_data) > offset >= 0 == offset % 4:
            lut_data = self.rom_data[offset:(offset + (count * 4))]
            return struct.unpack(f"<{count}I", lut_data)

        if offset % 4 != 0:
            raise RuntimeError(f"Offset must be word aligned: {hex(offset)}")
        raise RuntimeError(f"Index out of bounds {hex(offset)} vs {len(self.rom_data)}")

    def write(self, path: str):
        with open(path, "wb") as rom_file:
            rom_file.write(self.rom_data)
            rom_file.close()

    @staticmethod
    def pointer_to_offset(pointer):
        if pointer >= 0x8000000:
            return pointer - 0x8000000
        raise RuntimeError(f"Not a pointer {hex(pointer)}")
