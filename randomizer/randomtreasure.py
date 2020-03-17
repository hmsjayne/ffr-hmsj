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

from doslib.maps import TreasureChest, MoneyChest, ItemChest
from doslib.rom import Rom
from randomizer.treasurebuckets import TreasureBuckets
from stream.outputstream import OutputStream


def random_bucketed_treasures(rom: Rom, rng: Random, wealth_level: int = 0) -> Rom:
    """Randomly generates and shuffles treasured based on wealth_level"""
    bucket_data = TreasureBuckets()
    chest_stream = rom.open_bytestream(0x217FB4, 0x400)
    chests_to_shuffle = []
    original_list = []
    money_count = 0
    item_total = 0
    for index in range(256):
        chest = TreasureChest.read(chest_stream)
        original_list.append(chest)
        if isinstance(chest, ItemChest):
            if chest.item_type != 0:
                item_bucket = bucket_data.get_bucket(chest.item_type, chest.item_id)
                if wealth_level == 1:
                    item_bucket = bucket_data.up_one(item_bucket)
                if wealth_level == -1:
                    item_bucket = bucket_data.down_one(item_bucket)
                new_item = bucket_data.pull_from_bucket(item_bucket, rng, 1)
                chest.item_id = new_item[0]
                item_total += 1
                chests_to_shuffle.append(chest)
        elif isinstance(chest, MoneyChest):
            chest.qty = rng.randint(1, 0xfff) * rng.randint(1, 6)
            chests_to_shuffle.append(chest)
            money_count += 1
        else:
            print("BAD CHEST")
    rng.shuffle(chests_to_shuffle)

    chest_data = OutputStream()
    for chest in original_list:
        if isinstance(chest, MoneyChest) or chest.item_type != 0:
            new_chest = chests_to_shuffle.pop()
            new_chest.write(chest_data)
        else:
            chest.write(chest_data)

    return rom.apply_patch(0x217FB4, chest_data.get_buffer())
