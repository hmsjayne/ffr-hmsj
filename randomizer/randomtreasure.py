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
from stream.outputstream import OutputStream
from randomizer.treasurebuckets import TreasureBuckets

#Pure random - easy enough.
# 0x01 ->
#Armor 0x46
#Weapon 0x40
#Item 0x2B
#We'll keep the same ratio of money to items

def random_treasures(rom: Rom, rng: Random) -> Rom:
    chest_stream = rom.open_bytestream(0x217FB4, 0x400)
    items = [(0,x + 1) for x in list(range(0x45))]
    items = items + [(1,x + 1) for x in list(range(0x3F))]
    items = items + [(2,x + 1) for x in list(range(0x2A))]
    itemCount = len(items)
    print(itemCount)
    chests_to_shuffle = []
    original_list = []
    moneyCount = 0
    itemTotal = 0
    for index in range(256):
        chest = TreasureChest.read(chest_stream)
        original_list.append(chest)
        if isinstance(chest, ItemChest):
            if chest.item_type != 0:
                new_item = items[rng.randint(0,itemCount-1)]
                chest.item_type = new_item[0]
                chest.item_id = new_item[1]
                itemTotal += 1
                chests_to_shuffle.append(chest)
        elif isinstance(chest, MoneyChest):
            chest.qty = rng.randint(1, 0xfff) * rng.randint(1,6)
            chests_to_shuffle.append(chest)
            print(chest.qty)
            moneyCount += 1
        else:
            print("BAD CHEST")
    return
    rng.shuffle(chests_to_shuffle)

    chest_data = OutputStream()
    for chest in original_list:
        if isinstance(chest, MoneyChest) or chest.item_type != 0:
            new_chest = chests_to_shuffle.pop()
            new_chest.write(chest_data)
        else:
            chest.write(chest_data)

    return rom.apply_patch(0x217FB4, chest_data.get_buffer())

def random_bucketed_treasures(rom: Rom, rng: Random, wealth_level: int=0) -> Rom:
    """Randomly generates and shuffles treasured based on wealth_level"""
    bucket_data = TreasureBuckets()
    chest_stream = rom.open_bytestream(0x217FB4, 0x400)
    items = [(0,x + 1) for x in list(range(0x45))]
    items = items + [(1,x + 1) for x in list(range(0x3F))]
    items = items + [(2,x + 1) for x in list(range(0x2A))]
    itemCount = len(items)
    chests_to_shuffle = []
    original_list = []
    moneyCount = 0
    itemTotal = 0
    for index in range(256):
        chest = TreasureChest.read(chest_stream)
        original_list.append(chest)
        if isinstance(chest, ItemChest):
            if chest.item_type != 0:
                item_bucket = bucket_data.getBucket(chest.item_type, chest.item_id)
                if wealth_level == 1:
                    item_bucket = bucket_data.up_one(item_bucket)
                if wealth_level == -1:
                    item_bucket = bucket_data.down_one(item_bucket)
                new_item = bucket_data.pullFromBucket(item_bucket,rng, 1)
                chest.item_id = new_item[0]
                itemTotal += 1
                chests_to_shuffle.append(chest)
        elif isinstance(chest, MoneyChest):
            chest.qty = rng.randint(1, 0xfff) * rng.randint(1,6)
            chests_to_shuffle.append(chest)
            moneyCount += 1
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
