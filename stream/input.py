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


class Input(object):
    """Class to present a bytearray as a stream"""

    def __init__(self, stream: bytearray, check_alignment: bool = True):
        self.index = 0
        self.stream = stream
        self.check_alignment = check_alignment

    def is_eos(self):
        """Checks if the stream has ended

        :return: True if the stream has ended, False otherwise
        """
        return not self.index < len(self.stream)

    def get_u8(self):
        """Gets a byte from the stream

        :return: The byte, or None if the stream has ended.
        """
        if self.index < len(self.stream):
            char = self.stream[self.index]
            self.index += 1
        else:
            char = None
        return char

    def get_u16(self):
        """Gets a short (16 bits) from the stream

        :return: The short, or None if the stream has ended.
        """
        if self.index < len(self.stream):
            if self.check_alignment:
                self._ensure_halfword_aligned()

            data = self.stream[self.index:self.index + 2]
            self.index += 2
            return int.from_bytes(data, byteorder="little", signed=False)
        else:
            return None

    def get_u32(self):
        """Gets an int (32 bits) from the stream

        :return: The int, or None if the stream has ended.
        """
        if self.index < len(self.stream):
            if self.check_alignment:
                self._ensure_word_aligned()

            data = self.stream[self.index:self.index + 4]
            self.index += 4
            return int.from_bytes(data, byteorder="little", signed=False)
        elif self.index % 4 != 0:
            raise RuntimeError(f"Offset must be word aligned: {hex(self.index)}")
        else:
            return None

    def unget_u8(self):
        """ Puts a the last byte read back into the stream."""
        if self.index > 0:
            self.index -= 1

    def unget_u16(self):
        """ Puts a the last short read back into the stream."""
        if self.check_alignment:
            self._ensure_halfword_aligned()

        if self.index > 0:
            self.index -= 2

    def unget_u32(self):
        """ Puts a the last int read back into the stream."""
        if self.check_alignment:
            self._ensure_word_aligned()
        if self.index > 0:
            self.index -= 4

    def _ensure_halfword_aligned(self):
        if self.index % 2 != 0:
            raise RuntimeError(f"Offset must be half-word aligned: {hex(self.index)}")

    def _ensure_word_aligned(self):
        if self.index % 4 != 0:
            raise RuntimeError(f"Offset must be word aligned: {hex(self.index)}")
