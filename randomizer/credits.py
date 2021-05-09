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

from doslib.rom import Rom
from doslib.textblock import TextBlock
from randomizer.flags import Flags
from stream.outputstream import OutputStream


def add_credits(rom: Rom, seed: str, flags: Flags) -> dict:
    credits_lut = rom.get_lut(0x1D871C, 128)
    base_addr = credits_lut[0]

    new_lut = OutputStream()
    data_stream = OutputStream()

    for index, line in enumerate(CREDITS_TEXT.splitlines()[1:]):
        line = line.strip()
        if len(line) > 0:
            encoded = TextBlock.encode_text(line)

            new_lut.put_u32(base_addr + data_stream.size())
            data_stream.put_bytes(encoded)
        else:
            new_lut.put_u32(0x0)

    # And EOF marker
    new_lut.put_u32(0xffffffff)

    # Change the duration so it doesn't take so long to scroll
    duration = OutputStream()
    duration.put_u16(60 * 60)

    # We need to clean up the seed since this string is from untrusted input
    # (It was untrusted the entire time, but this is the first time it matters)
    safe_seed = ""
    values = list(TextBlock.INVERTED_TEXT_TABLE.values())
    for char in seed:
        if char in TextBlock.INVERTED_TEXT_TABLE:
            safe_seed += char
        else:
            encode_as = f"\\u{hex(values[ord(char) % len(values)])[2:]}"
            safe_seed += encode_as

    # Little extra processing
    safe_seed = safe_seed.replace("\\u82583", "\\u82D0")

    # Add the seed + flags to the party creation screen.
    seed_str = TextBlock.encode_text(f"Check:\n{safe_seed}\nFlags:\n{flags.encode()}\x00")
    pointer = OutputStream()
    pointer.put_u32(0x8227054)

    return {
        # Credits update
        0x016848: duration.get_buffer(),
        0x1D871C: new_lut.get_buffer(),
        Rom.pointer_to_offset(base_addr): data_stream.get_buffer(),

        # Show flags + seed
        0x227054: seed_str,
        0x4d8d4: pointer.get_buffer()
    }


CREDITS_TEXT = """
Thank you for playing
Final Fantasy: HMS Jayne!




A proof of concept
randomizer designed by
nic0lette




Developers:
nic0lette
Vennobennu
leggystarscream




Website Design:
Seelie Fae




Playtest:
Demerine
leggystarscream
rabite





"""
