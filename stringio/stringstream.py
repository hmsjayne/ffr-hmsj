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


class StringStream(object):
    """Class for managing a string like a C input stream"""

    def __init__(self, stream: str):
        self.stream = stream
        self.index = 0

    def is_eos(self):
        """Checks if the stream has ended

        :return: True if the stream has ended, False otherwise
        """
        return not self.index < len(self.stream)

    def getc(self):
        """Gets a character from the stream

        :return: The character, or None if the stream has ended.
        """
        if self.index < len(self.stream):
            char = self.stream[self.index]
            self.index += 1
        else:
            char = None
        return char

    def ungetc(self):
        """ Puts a the last character read back into the stream."""
        if self.index > 0:
            self.index -= 1
