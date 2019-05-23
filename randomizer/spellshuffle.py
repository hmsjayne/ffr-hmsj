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
import copy

from random import Random
from doslib.rom import Rom
from doslib.shopdata import ShopData
from doslib.spells import Spells
from randomizer.shuffledlist import ShuffledList
from stream.outputstream import OutputStream


class SpellShuffle(object):
    def __init__(self, rom: Rom, rng: Random):
        self._shops = ShopData(rom)
        self._spells = Spells(rom)

        self._permissions = []
        permissions_stream = rom.open_bytestream(0x1A20C0, 0x82)
        while not permissions_stream.is_eos():
            self._permissions.append(permissions_stream.get_u16())

        self._do_shuffle(rng)

    def write(self, rom: Rom) -> Rom:
        permissions_stream = OutputStream()
        for permission in self._permissions:
            permissions_stream.put_u16(permission)

        rom = rom.apply_patch(0x1A20C0, permissions_stream.get_buffer())
        rom = self._spells.write(rom)
        return self._shops.write(rom)

    def _do_shuffle(self, rng: Random):
        white_magic_offset = 1
        black_magic_offset = white_magic_offset + 32

        # To keep the game a _bit_ sane, split out white + black magic
        # and shuffle each independently.
        white_magic = ShuffledList(self._spells[1:33], rng)
        black_magic = ShuffledList(self._spells[33:65], rng)

        # We want to be very lazy with how we shuffle spells in the game.
        # Specifically, there are a bunch of additional tables, such as the name table,
        # the graphics lookup table, and even the items that cast these spells.
        #
        # Rather than write a complete new table, with the spells in a different order,
        # we leave all the spells in the same order, but change their levels, and
        # which shop sells which spell.
        #
        # NOTE: This is only possible because of the patch "SpellLevelFix.ips" in the
        # data directory, created by @Vennobennu.
        #
        # Since we want to create a new list, with values getting changed, such as
        # spell level and cost, we create a deep copy of the list first, and then
        # do the updates.
        # After we're done, we drop the original, unshuffled version.
        new_spells_list = copy.deepcopy(self._spells)

        # This is a simple mapping from original spell slot to the shuffled slot.
        # We build this up so that magic is sold in different shops, which completes
        # the "shuffle" effect.
        #
        # For example. Let's imagine that "Holy", spell 30, and "Cure", spell 1 were
        # swapped. This would be reflected in "complete_magic_mapping" like this:
        #
        # complete_magic_mapping[1] = 30
        # ...
        # complete_magic_mapping[30] = 1
        #
        # Then, when the shop inventories are updated, you'd find "Holy" on sale in
        # Cornelia, and "Cure" for sale in Lefein.
        complete_magic_mapping = list()
        complete_magic_mapping.append(0)

        for index, magic in enumerate(white_magic):
            spell_index = white_magic.original_index(index) + white_magic_offset
            new_spells_list[spell_index].level = int(index / 4) + 1
            new_spells_list[spell_index].price = self._spells[index + white_magic_offset].price
            new_spells_list[spell_index].mp_cost = self._spells[index + white_magic_offset].mp_cost
            complete_magic_mapping.append(spell_index)

        for index, magic in enumerate(black_magic):
            spell_index = black_magic.original_index(index) + black_magic_offset
            new_spells_list[spell_index].level = int(index / 4) + 1
            new_spells_list[spell_index].price = self._spells[index + black_magic_offset].price
            new_spells_list[spell_index].mp_cost = self._spells[index + black_magic_offset].mp_cost
            complete_magic_mapping.append(spell_index)

        # Now that we've finished with the code that needs to look back at the original spell list,
        # we can swap in the shuffled version.
        # REMEMBER! The order of the spells is the same as vanilla, only their level data has been
        # changed to support this. (Though other values may have changed ;)
        self._spells = new_spells_list

        # To keep things simple, map the new spell inventories directly to the shuffled slots with
        # the mapping created above.
        for shop_number, inventory in enumerate(self._shops.shop_inventories):
            if shop_number in [0x26, 0x27]:
                # Shop 0x26 is the "Bottle" shop and 0x27 is the item shop that opens
                # after the Bottle has been purchased.
                continue
            if len(inventory.magic) > 0:
                new_magic_inventory = []
                for spell_index in inventory.magic:
                    new_magic_inventory.append(complete_magic_mapping[spell_index])
                inventory.magic = new_magic_inventory

        # Finally, rewrite permissions to be the same as the slot was before.
        new_permissions = copy.deepcopy(self._permissions)
        for index, magic in enumerate(self._spells):
            new_permissions[complete_magic_mapping[index]] = self._permissions[index]
        self._permissions = new_permissions
