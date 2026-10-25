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

from randomizer.treasure import InventoryGenerator


def get_random_inventory_for_shop(map_index: int, shop_type: str, count: int, ids: bool,
                                  inventory_generator: InventoryGenerator) -> list:
    new_items = []

    # Cornelia Item Shop gets special treatment
    if map_index == 0x3E:
        items = inventory_generator.items.get_by_type("item")

        # Ensure Antidote and Gold Needle are in Cornelia
        new_items.append(items[0xb])
        new_items.append(items[0xc])

        # Make sure there aren't too many items there...
        count = max(count, 3)

    while len(new_items) < count:
        new_item = inventory_generator.get_inventory(map_index, shop_type)
        if new_item not in new_items:
            new_items.append(new_item)

    if ids:
        new_inventory = []
        for item in sorted(new_items, key=lambda it: it.sort_order):
            new_inventory.append(item.id)
        return new_inventory
    else:
        return new_items


def randomize_shops(rng, maps, shops, inventory_generator: InventoryGenerator):
    for map_index in range(1, 0x76):
        map_features = maps.get_map(map_index)
        if len(map_features.shops) < 1:
            continue

        for shop_feature in map_features.shops:
            shop_inventories = shops.shop_inventories[shop_feature.event]

            if len(shop_inventories.items) > 0:
                count = rng.randint(3, 5)
                shop_inventories.items = get_random_inventory_for_shop(map_index, "item", count, True,
                                                                       inventory_generator)
            if len(shop_inventories.weapons) > 0:
                count = rng.randint(3, 5)
                items = get_random_inventory_for_shop(map_index, "weapon", count, False,
                                                      inventory_generator)
                items.sort(key=lambda it: it.sort_order)
                shop_inventories.weapons = list(map(lambda it: it.id, items))
            if len(shop_inventories.armor) > 0:
                count = rng.randint(3, 5)
                items = get_random_inventory_for_shop(map_index, "armor", count, False,
                                                      inventory_generator)
                items.sort(key=lambda it: it.sort_order)
                shop_inventories.armor = list(map(lambda it: it.id, items))
            elif len(shop_inventories.magic) > 0:
                # Magic shops don't get randomized as much as shuffled...
                continue
