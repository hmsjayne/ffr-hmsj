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

from random import Random

from doslib.maps import TreasureChest, MoneyChest
from doslib.rom import Rom
from stream.outputstream import OutputStream



def treasure_shuffle(rom: Rom, rng: Random) -> Rom:
    chest_stream = rom.open_bytestream(0x217FB4, 0x400)

    chests_to_shuffle = []
    original_list = []
    for index in range(256):
        chest = TreasureChest.read(chest_stream)
        original_list.append(chest)
        if isinstance(chest, MoneyChest) or chest.item_type != 0:
            chests_to_shuffle.append(chest)

    rng.shuffle(chests_to_shuffle)

    chest_data = OutputStream()
    for chest in original_list:
        if isinstance(chest, MoneyChest) or chest.item_type != 0:
            new_chest = chests_to_shuffle.pop()
            new_chest.write(chest_data)
        else:
            chest.write(chest_data)

    return rom.apply_patch(0x217FB4, chest_data.get_buffer())