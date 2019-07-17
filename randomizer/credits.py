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
from stream.outputstream import OutputStream


def add_credits(rom: Rom) -> Rom:
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

    return rom.apply_patches({
        0x016848: duration.get_buffer(),
        0x1D871C: new_lut.get_buffer(),
        Rom.pointer_to_offset(base_addr): data_stream.get_buffer()
    })


CREDITS_TEXT = """
Thank you for playing
Final Fantasy: HMS Jayne!




A proof of concept
randomizer designed by
Nicole Borrelli




Developers:
Nicole Borrelli
Vennobennu
leggystarscream




Website Design:
a tiny fairy




Playtest:
Demerine
leggystarscream

"""
