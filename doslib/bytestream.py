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


class ByteStream(object):
    """Class to present a bytearray as a stream"""

    def __init__(self, stream: bytearray):
        self.stream = stream
        self.index = 0

    def is_eos(self):
        """Checks if the stream has ended

        :return: True if the stream has ended, False otherwise
        """
        return not self.index < len(self.stream)

    def getc(self):
        """Gets a byte from the stream

        :return: The byte, or None if the stream has ended.
        """
        if self.index < len(self.stream):
            char = self.stream[self.index]
            self.index += 1
        else:
            char = None
        return char

    def get_short(self):
        if self.index < len(self.stream) and self.index % 2 == 0:
            data = self.stream[self.index:self.index + 2]
            self.index += 2
            return int.from_bytes(data, byteorder="little", signed=False)
        elif self.index % 2 != 0:
            raise RuntimeError(f"Offset must be half-word aligned: {hex(self.index)}")
        else:
            return None

    def get_int(self):
        if self.index < len(self.stream) and self.index % 4 == 0:
            data = self.stream[self.index:self.index + 4]
            self.index += 4
            return int.from_bytes(data, byteorder="little", signed=False)
        elif self.index % 4 != 0:
            raise RuntimeError(f"Offset must be word aligned: {hex(self.index)}")
        else:
            return None

    def ungetc(self):
        """ Puts a the last byte read back into the stream."""
        if self.index > 0:
            self.index -= 1
