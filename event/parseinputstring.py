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


class ParseInputString(object):
    """Class to parse a string with an API similar to C."""

    def __init__(self, data: str):
        self._data = data
        self._index = 0

    def getc(self):
        char = self.peek()
        if char is not None:
            self._index += 1
        return char

    def ungetc(self):
        if self._index > 0:
            self._index -= 1

    def peek(self):
        if self._index < len(self._data):
            return self._data[self._index]
        else:
            return None

    def get_int(self) -> int:
        working = ""
        is_hex = False

        char = self.getc()
        while char is not None and (char.isdigit() or (is_hex and char.lower() in ['a', 'b', 'c', 'd', 'e', 'f'])):
            working += char

            char = self.getc()

            # Special case for hex number
            if len(working) == 1 and (char == 'x' or char == 'X'):
                is_hex = True
                working += char
                char = self.getc()

        if is_hex:
            return int(working, 16)
        else:
            return int(working)

    def get_alphanum_str(self, additional_allowed: list = []) -> str:
        # Identifiers are alphanumeric, but start with a letter. They may include '_' because ... Python?
        current = ""
        char = self.getc()
        while char is not None and (char.isalnum() or char in additional_allowed):
            current += char
            char = self.getc()

        # Took one too many characters, potentially.
        if char is not None:
            self.ungetc()

        # Return what we got
        return current
