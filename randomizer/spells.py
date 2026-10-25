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

from copy import deepcopy

from randomizer.spellgenerator import SpellGenerator


def spell_shuffle(maps, shops, spells, spell_generator: SpellGenerator):
    original_spells = deepcopy(spells)
    for map_index in range(1, 0x76):
        map_features = maps.get_map(map_index)
        if len(map_features.shops) < 1:
            continue

        # Don't touch the caravan.
        if map_index in [0x72, 0x73]:
            continue

        for shop_feature in map_features.shops:
            shop_inventories = shops.shop_inventories[shop_feature.event]
            if len(shop_inventories.magic) == 0:
                continue

            new_inventory = []
            first_spell = shop_inventories.magic[0]
            school = "white" if first_spell <= 32 else "black"
            spell_level = int(first_spell / 4) + 1 if school == "white" else int((first_spell - 32) / 4) + 1
            for slot_index in range(0, len(shop_inventories.magic)):
                spell_index = shop_inventories.magic[slot_index]
                spell = spell_generator.get_inventory(map_index, school)
                orig_spell = original_spells.spell_data[spell_index]

                # Put the spell for sale in this shop
                new_inventory.append(spell.spell_index)

                # Update the level of the spell for real
                spells.spell_data[spell.spell_index].level = spell_level
                spells.spell_data[spell.spell_index].price = orig_spell.price
                if spell_level <= 2:
                    spells.spell_data[spell.spell_index].mp_cost = orig_spell.mp_cost

                spells.permissions[spell.spell_index] = spells.shuffled_permission[spell_index]
            shop_inventories.magic = new_inventory
