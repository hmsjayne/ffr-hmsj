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

import copy
from collections import namedtuple
from doslib.dos_utils import load_tsv
from doslib.item import Item, Weapon, Armor
from doslib.rom import Rom
from stream.outputstream import OutputStream

ItemDataExtra = namedtuple("ItemDataExtra",
                           ["type", "item_index", "name", "cost", "sale_price", "is_soc", "grade"])


class Items(object):
    def __init__(self, rom: Rom, new_weights: bool):
        self.by_type = [
            [],  # dummy
            [],  # items
            [],  # weapons
            [],  # armor
        ]

        item_stream = rom.open_bytestream(0x19f07c, 0x19f33c - 0x19f07c)
        while not item_stream.is_eos():
            self.by_type[1].append(Item(item_stream))
        weapon_stream = rom.open_bytestream(0x19f33c, 0x19fa57 - 0x19f33c)
        while not weapon_stream.is_eos():
            self.by_type[2].append(Weapon(weapon_stream))
        armor_stream = rom.open_bytestream(0x19fa58, 0x1a021b - 0x19fa58)
        while not armor_stream.is_eos():
            self.by_type[3].append(Armor(armor_stream))
        data_file = "data/ItemData_2.tsv" if new_weights else "data/ItemData.tsv"

        for item_data in load_tsv(data_file):
            extra = ItemDataExtra(*item_data)

            index = Items.name_to_index(extra.type)
            item_list = self.by_type[index]

            # Add extra data to items
            item_list[extra.item_index].id = extra.item_index
            item_list[extra.item_index].item_type = extra.type
            item_list[extra.item_index].name = extra.name
            item_list[extra.item_index].is_soc = extra.is_soc
            item_list[extra.item_index].grade = extra.grade

            # And update items with some data of our own
            item_list[extra.item_index].cost = extra.cost
            item_list[extra.item_index].sale_price = extra.sale_price

    def all(self):
        all_items = {}
        for type_index in range(1, 4):
            all_items[Items.index_to_name(type_index)] = self.by_type[type_index]
        return all_items

    def get_by_type(self, type_name: str) -> list:
        return self.by_type[Items.name_to_index(type_name)]

    def find_by_type(self, type_name: str, item_name: str) -> Item:
        for item in self.by_type[Items.name_to_index(type_name)]:
            if item.name == item_name:
                return item
        return None

    def get_patches(self) -> dict:
        item_out = OutputStream()
        for item in self.by_type[1]:
            item.write(item_out)
        weapon_out = OutputStream()
        for weapon in self.by_type[2]:
            weapon.write(weapon_out)
        armor_out = OutputStream()
        for armor in self.by_type[3]:
            armor.write(armor_out)

        return {
            0x19f07c: item_out.get_buffer(),
            0x19f33c: weapon_out.get_buffer(),
            0x19fa58: armor_out.get_buffer(),
        }

    @staticmethod
    def downgrade_item(item: Item):
        downgrade = copy.deepcopy(item)
        downgrade.grade = chr(ord(item.grade[0]) + 1)
        return downgrade

    @staticmethod
    def name_to_index(name: str) -> int:
        name_to_index = {
            "item": 1,
            "weapon": 2,
            "armor": 3
        }
        return name_to_index[name]

    @staticmethod
    def index_to_name(index: int) -> str:
        index_to_name = ["dummy", "item", "weapon", "armor"]
        return index_to_name[index]
