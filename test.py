#!/usr/bin/env python3

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

import sys
from random import seed, randint

from doslib.rom import Rom


def main(argv):
    rom = Rom(argv[0])

    if len(argv) > 1:
        rom_seed = argv[1]
    else:
        rom_seed = hex(randint(0, 0xffffffff))

    seed(seed)

    event_text_lut = rom.get_lut(0x211770, 100)
    for loc in event_text_lut:
        print(f"Entry: {hex(loc)}")

    stream = rom.open_bytestream(0x211770, 0x400)
    print(f"first int: {hex(stream.get_short())}")

if __name__ == "__main__":
    main(sys.argv[1:])
