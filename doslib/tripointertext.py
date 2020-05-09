#  Copyright 2020 Nicole Borrelli
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


class TriPointerTextBlock(TextBlock):
    """
    Dawn of Souls makes relatively frequent use of a 3-pointer
    text block. In this format, the first and second pointers are
    often used for the name of the thing, and the 3rd for its
    description.
    Items, Armor, Weapons, and Key Items all use this format.
    """

    def __init__(self, rom: Rom, lut_offset: int, count: int):
        # There are 3 pointers per item
        super().__init__(rom, lut_offset, count * 3)

    def __getitem__(self, index: int):
        return super().__getitem__(index * 3)

    def __setitem__(self, index: int, value: str):
        return super().__setitem__(index * 3, value)

    def get_description(self, index: int):
        return super().__getitem__((index * 3) + 2)

    def set_description(self, index: int, value: str):
        return super().__setitem__(index * 3, value)

    def size(self):
        return len(self.strings)
