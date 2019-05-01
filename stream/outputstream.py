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


class OutputStream(object):
    """Class to present a bytearray as a stream"""

    def __init__(self, max_size: int = None):
        self._stream = bytearray()
        self._max_size = max_size

    def get_buffer(self) -> bytearray:
        return self._stream

    def size(self) -> int:
        """Gets the currently used size of the buffer in bytes.

        :return: Number of bytes currently used.
        """
        return len(self._stream)

    def put_u8(self, data: int):
        self._stream.append(data)

    def put_u16(self, data: int):
        self._stream.extend(int.to_bytes(data, 2, byteorder="little", signed=False))

    def put_u32(self, data: int):
        self._stream.extend(int.to_bytes(data, 4, byteorder="little", signed=False))

    def put_bytes(self, data: bytearray):
        self._stream.extend(data)

    def _ensure_halfword_aligned(self):
        if len(self._stream) % 2 != 0:
            raise RuntimeError(f"Offset must be half-word aligned: {hex(len(self._stream))}")

    def _ensure_word_aligned(self):
        if len(self._stream) % 4 != 0:
            raise RuntimeError(f"Offset must be word aligned: {hex(len(self._stream))}")

    def _check_size(self):
        if self._max_size is not None and len(self._stream) >= self._max_size:
            raise RuntimeError(f"Stream overrun: {len(self._stream)} bytes of {self._max_size}")


class AddressableOutputStream(OutputStream):
    def __init__(self, base_addr: int = 0, max_size: int = None):
        super().__init__(max_size)
        self._base_addr = base_addr

    def current_addr(self):
        return self._base_addr + len(self._stream)
