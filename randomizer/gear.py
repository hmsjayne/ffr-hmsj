#  Copyright 2026 HMS Jayne contributors
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

from doslib.item import Item
from randomizer.treasure import InventoryGenerator


def randomize_starting_gear(rng, items, classes_data: list) -> list:
    base_weapons = []
    base_armors = []

    # Find weapons & armor that can be used by the base classes
    # Also cap the power level of the gear
    for weapon in items.get_by_type("weapon"):
        if weapon.id > 0 and weapon.equip_classes & 0x003f != 0:
            base_weapons.append(weapon)
    for armor in items.get_by_type("armor"):
        if 0x1b >= armor.id > 0 != armor.equip_classes & 0x003f:
            base_armors.append(armor)

    class_bit = 0x1
    for class_data in classes_data:
        class_weapons = []
        class_armors = []
        for weapon in base_weapons:
            if weapon.equip_classes & class_bit != 0:
                class_weapons.append(weapon)
        for armor in base_armors:
            if armor.equip_classes & class_bit != 0:
                class_armors.append(armor)
        class_data.weapon_id = rng.choice(class_weapons).id
        class_data.armor_id = rng.choice(class_armors).id
        class_bit = class_bit << 1

    return classes_data


def pick_gear_reward(rng, gear_placement, inventory_generator: InventoryGenerator) -> Item:
    gear_type = rng.choice(["weapon", "armor"])
    grades = ["S", "A"] if gear_placement.zone in ["inner", "early"] else ["S"]
    options = []
    for grade in grades:
        if grade in inventory_generator.item_grades:
            for item in inventory_generator.item_grades[grade]:
                if item.item_type == gear_type:
                    options.append(item)

    choice = rng.choice(options)
    if gear_placement.zone == "early":
        # If the gear falls onto the King, Sara, or Bikke, make sure at least one unpromoted class can use it
        while choice.equip_classes & 0x3f == 0:
            choice = rng.choice(options)
    return choice
