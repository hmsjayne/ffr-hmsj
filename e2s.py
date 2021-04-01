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

from argparse import ArgumentParser

from doslib.rom import Rom
from event.e2s import disassemble_event


def main():
    parser = ArgumentParser(description="Final Fantasy: Dawn of Souls Event->Script")
    parser.add_argument("rom", metavar="ROM file", type=str, help="ROM source file")
    parser.add_argument("--event", dest="event", type=str, help="Event to disassemble")
    parsed = parser.parse_args()

    # Opening the ROM is simple.
    rom = Rom(parsed.rom)

    # The event id is a bit trickier. The parser won't recognize hex values, so we need to accept it as a
    # string and convert it ourselves.
    if parsed.event.startswith("0x"):
        event_id = int(parsed.event, 16)
    else:
        event_id = int(parsed.event)

    disassemble_event(rom, event_id)


if __name__ == "__main__":
    main()
