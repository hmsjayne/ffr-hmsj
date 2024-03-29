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
from collections import namedtuple

from stream.inputstream import InputStream


class Rom(object):
    """Class that represents a Dawn of Souls ROM."""

    def __init__(self, data: bytearray = None):
        self.rom_data = data
        self._free_block = FreeBlock(0x8223F4C, 0x1860)

    def open_bytestream(self, offset: int, size: int = -1, check_alignment: bool = True) -> InputStream:
        """
        Opens a InputStream to read over part of the ROM.
        :param offset: Offset of the start of the InputStream
        :param size: Number of bytes to include
        :param check_alignment: Whether non-byte reads should checked that they are word aligned
        :return: The InputStream
        """
        if 0 <= offset < len(self.rom_data):
            data = self.rom_data[offset:] if size < 0 else self.rom_data[offset:(offset + size)]
            return InputStream(data, check_alignment=check_alignment)
        raise RuntimeError(f"Index out of bounds {hex(offset)} vs {len(self.rom_data)}")

    def get_lut(self, offset: int, count: int) -> tuple:
        """Gets a look-up table from the ROM.

        Note: The offset *must* be word aligned as all the LUTs in the ROM are.

        :param offset: Offset of the lookup table
        :param count: Number of pointers to read
        :return: The LUT as a tuple
        """
        if len(self.rom_data) > offset >= 0 == offset % 4:
            lut_data = self.rom_data[offset:(offset + (count * 4))]
            return struct.unpack(f"<{count}I", lut_data)

        if offset % 4 != 0:
            raise RuntimeError(f"Offset must be word aligned: {hex(offset)}")
        raise RuntimeError(f"Index out of bounds {hex(offset)} vs {len(self.rom_data)}")

    def get_string(self, offset) -> bytearray:
        """
        Gets a null terminated string.
        :param offset: Offset of the string to read.
        :return: The string as a bytearray.
        """
        end_offset = offset
        while self.rom_data[end_offset] != 0x0:
            end_offset += 1
        return self.rom_data[offset:end_offset + 1]

    def get_stream(self, offset: int, end_marker: bytearray) -> InputStream:
        """
        Gets an InputStream from the ROM.

        This should primarily be used where the data is not null terminated (use `get_string` then), and is of
        variable length. Many events could be read using this method and a bytearray of [0x0, 0x4, 0xff, 0xff]
        for example, but `get_event` should be used in that case.

        :param offset: The offset of the start of the stream.
        :param end_marker: The end marker.
        :return: InputStream representing the data.
        """
        end_offset = offset
        markers_found = 0

        while markers_found < len(end_marker):
            if self.rom_data[end_offset] == end_marker[markers_found]:
                markers_found += 1
            else:
                markers_found = 0
            end_offset += 1

        return InputStream(self.rom_data[offset:end_offset])

    def apply_patches(self, patches):
        """Applies a set of patches to a the rom.

        :param patches: Patches to apply as a dictionary. Keys are offsets, values are patch data.
        :return: A patched version of the rom.
        """
        new_data = bytearray()

        working_offset = 0
        for offset in sorted(patches.keys()):
            if working_offset > offset:
                raise RuntimeError(f"Could not apply patch to {hex(offset)}; already at {hex(working_offset)}!")
            elif offset > len(self.rom_data):
                raise RuntimeError(f"Invalid patch offset {hex(offset)}! Is it a pointer?")

            # Check if there's missing data between our working position and the next patch
            if working_offset < offset:
                new_data.extend(self.rom_data[working_offset:offset])

            # Now that we're caught up, plop the patch in, and update the working offset.
            patch = patches[offset]
            new_data.extend(patch)
            working_offset = offset + len(patch)

        # Now that the patches are applied, add whatever is left of the file.
        new_data.extend(self.rom_data[working_offset:])

        return Rom(data=new_data)

    def get_event_size(self, offset: int) -> int:
        """
        Naively calculates the size of an event.

        Note: This does *not* follow jumps. Many events only include one "end of event" command at the end,
        and this method will work to read them. Some SoC events, however, include multiple end of event commands,
        and this method would only read to the first one.

        :param offset: Offset of the start of the event.
        :return: InputStream representing the event.
        """
        if Rom._is_pointer(offset):
            offset = Rom.pointer_to_offset(offset)

        end_offset = offset
        last_cmd = -1
        while last_cmd != 0:
            cmd_len = self.rom_data[end_offset + 1]
            last_cmd = self.rom_data[end_offset]
            end_offset += cmd_len

        return end_offset - offset

    def get_free_space(self, owner: str, size: int) -> int:
        return self._free_block.allocate(owner, size)

    @staticmethod
    def pointer_to_offset(pointer: int) -> int:
        """
        Converts a pointer to an offset.
        :param pointer: Pointer to convert.
        :return: Offset in the ROM file.
        """
        if Rom._is_pointer(pointer):
            return pointer - 0x8000000
        raise RuntimeError(f"Not a pointer {hex(pointer)}")

    @staticmethod
    def offset_to_pointer(offset: int) -> int:
        """
        Converts a rom offset to a pointer.
        :param offset: Offset into the ROM.
        :return: A pointer representing the offset.
        """
        if offset <= 0x8000000:
            return offset + 0x8000000
        raise RuntimeError(f"Not a pointer {hex(offset)}")

    @staticmethod
    def _is_pointer(offset: int) -> int:
        return True if offset >= 0x8000000 else False


FreeBlockOwner = namedtuple("FreeBlockOwner", ["name", "address", "size"])


class FreeBlock(object):
    def __init__(self, base_addr: int, size: int):
        self._base_addr = base_addr
        self._total_size = size
        self._current_ptr = self._base_addr
        self._owners = []

    def allocate(self, owner: str, size: int) -> int:
        if self._remaining() >= size:
            owner = FreeBlockOwner(name=owner, address=self._current_ptr, size=size)
            self._current_ptr += size
            self._owners.append(owner)
            return owner.address
        else:
            print(f"No free space for alloc: {owner} needs {size} bytes; {self._remaining()} free")
            for allocated in self._owners:
                print(f"Allocated block: {allocated}")
            raise RuntimeError("No free space!")

    def _remaining(self):
        return self._total_size - (self._current_ptr - self._base_addr)
