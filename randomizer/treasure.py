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

import random
from collections import namedtuple
from copy import deepcopy

from doslib.dos_utils import load_tsv
from doslib.item import Item
from doslib.items import Items
from doslib.shopdata import ShopData

ChestData = namedtuple("ChestData", ["chest_index", "type", "contents", "description", "map", "grade", "notes"])

MapToArea = namedtuple("MapToArea", ["map_index", "name", "area"])


class InventoryGenerator(object):
    def __init__(self, seed: str, items: Items, new_distribution: bool):
        self.rng = random.Random()
        self.rng.seed(seed)

        self.items = deepcopy(items)

        self.chests_data = []
        chest_data_file = "data/ChestData.tsv"
        map_to_area_file = "data/MapToArea_2.tsv" if new_distribution else "data/MapToArea.tsv"
        area_weights_file = "data/AreaWeights_2.tsv" if new_distribution else "data/AreaWeights.tsv"
        for chest in load_tsv(chest_data_file):
            self.chests_data.append(ChestData(*chest))

        self.maps_to_area = {}
        for map_area in load_tsv(map_to_area_file):
            map_area_data = MapToArea(*map_area)
            self.maps_to_area[map_area_data.map_index] = map_area_data.area

        self.area_weights = {}
        for area_weight in load_tsv(area_weights_file):
            self.area_weights[area_weight[0]] = area_weight[1:]


        self.item_grades = {}
        for item_type in self.items.by_type:
            for item in item_type:
                if item.grade not in self.item_grades:
                    self.item_grades[item.grade] = []
                if item not in self.item_grades[item.grade]:
                    self.item_grades[item.grade].append(item)
        
        # Add gil chests too
        gil = Item()
        gil.item_type = "gil"
        num_gil_to_insert = 20
        for item_grade in ["B", "C", "D"]:
            for _ in range(0, num_gil_to_insert):
                self.item_grades[item_grade].append(gil)
            num_gil_to_insert += 10

    def update_with_new_shops(self, shop_data: ShopData):
        in_shops = {
            "item": [],
            "weapon": [],
            "armor": []
        }
        for shop_number, inventory in enumerate(shop_data.shop_inventories):
            # Stop after the Caravan, since the SoC shops are out of reach
            if shop_number > 0x75:
                break
            for item in inventory.items:
                in_shops["item"].append(item)
            for weapon in inventory.weapons:
                in_shops["weapon"].append(weapon)
            for armor in inventory.armor:
                in_shops["armor"].append(armor)

        for item_type, items in self.items.all().items():
            for item in items:
                if item.id in in_shops[item_type] and item.grade in ["C", "D"]:
                    item = Items.downgrade_item(item)
                if item.grade not in self.item_grades:
                    self.item_grades[item.grade] = []
                self.item_grades[item.grade].append(item)

    def get_inventory(self, map_index: int, item_type: str = None) -> Item:
        area = self.maps_to_area[map_index]
        area_weight = self.area_weights[area]
        #print(area_weight)
        index_to_letter = ["S", "A", "B", "C", "D", "E", "F"]

        item_pool = []
        while len(item_pool) < 1:
            chance = self.rng.randint(0, 100)
            pick = None
            for index, score in enumerate(area_weight):
                chance -= score
                if chance <= 0:
                    pick = index
                    break
            grade_letter = index_to_letter[pick]

            # If there's none at this letter grade, try to pick again
            if grade_letter not in self.item_grades:
                continue

            if item_type is None:
                item_pool = self.item_grades[grade_letter]
            else:
                item_pool = []
                for item in self.item_grades[grade_letter]:
                    if item.item_type == item_type:
                        item_pool.append(item)

            # If there's nothing left, try again
            if len(item_pool) < 1:
                continue
            return self.rng.choice(item_pool)


def _grade_to_score(grade: str) -> int:
    grades = {
        "S": 100,
        "A": 85,
        "B": 75,
        "C": 40,
        "D": 20,
    }
    base_grade = grades[grade[0]]
    if len(grade) > 1:
        if grade[1] == '+':
            return base_grade + 5
        else:
            return base_grade - 5
    return base_grade
