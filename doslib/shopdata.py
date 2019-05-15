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

from __future__ import annotations

from doslib.rom import Rom
from stream.inputstream import InputStream
from stream.outputstream import OutputStream


class ShopData(object):
    def __init__(self, rom: Rom):
        data_lut_stream = rom.open_bytestream(0x1DFB04, 0x198)
        self.shop_data_pointers = []
        self.shop_inventories = []
        for index in range(51):
            shop = ShopDataPointer(data_lut_stream)
            self.shop_data_pointers.append(shop)

            # This is overkill for vanilla, but is still small. Since code bytes don't count, the
            # value in shop.shop_data_length isn't quite as useful as it could be.
            inventory = ShopInventory(rom.open_bytestream(Rom.pointer_to_offset(shop.pointer), 0x20),
                                      shop.shop_data_length)
            self.shop_inventories.append(inventory)

    def write(self, rom: Rom) -> Rom:
        # Since there's a LUT and the data that it points to, create two output streams.
        # This should work because both are continuous.
        data_lut_stream = OutputStream()
        shop_inventory = OutputStream()

        next_shop_addr = self.shop_data_pointers[0].pointer
        start_size = 0
        for index in range(51):

            new_shop_length = self.shop_inventories[index].write(shop_inventory)
            sdp = self.shop_data_pointers[index]
            sdp.contents = ((sdp.shop_graphic << 4) & 0xf0) | (new_shop_length & 0x0f)
            sdp.pointer = next_shop_addr
            sdp.write(data_lut_stream)

            # Because the size of the data varies by shop, we have to keep track of how
            # large the output buffer was and move the pointer up by the difference.
            next_shop_addr += (shop_inventory.size() - start_size)
            start_size = shop_inventory.size()

        # Make a dictionary for the two parts so we only have to write the new Rom once.
        patches = {
            0x1E070C: data_lut_stream.get_buffer(),
            Rom.pointer_to_offset(self.shop_data_pointers[0].pointer): shop_inventory.get_buffer()
        }
        return rom.apply_patches(patches)


class ShopDataPointer(object):
    def __init__(self, stream: InputStream):
        self.contents = stream.get_u8()
        self.shop_graphic = (self.contents >> 4) & 0x0f
        self.shop_data_length = self.contents & 0x0f

        self.unused = []
        for unused in range(3):
            self.unused.append(stream.get_u8())
        self.pointer = stream.get_u32()

    def write(self, stream: OutputStream):
        stream.put_u8(self.contents)
        for data in self.unused:
            stream.put_u8(data)
        stream.put_u32(self.pointer)


class ShopInventory(object):
    def __init__(self, stream: InputStream, length: int):
        self.magic = []
        self.armor = []
        self.weapons = []
        self.items = []

        # There's no byte code for magic, so start there and change based on the data
        active = self.magic

        read_length = 0
        while read_length < length:
            data = stream.get_u8()
            if data == 0xfc:
                active = self.armor
            elif data == 0xfd:
                active = self.weapons
            elif data == 0xfe:
                active = self.items
            else:
                active.append(data)
                read_length += 1

    def write(self, stream: OutputStream) -> int:
        written_length = 0
        if len(self.magic) > 0:
            for magic_id in self.magic:
                stream.put_u8(magic_id)
                written_length += 1

        if len(self.armor) > 0:
            stream.put_u8(0xfc)
            for item_id in self.armor:
                stream.put_u8(item_id)
                written_length += 1

        if len(self.weapons) > 0:
            stream.put_u8(0xfd)
            for item_id in self.weapons:
                stream.put_u8(item_id)
                written_length += 1

        if len(self.items) > 0:
            stream.put_u8(0xfe)
            for item_id in self.items:
                stream.put_u8(item_id)
                written_length += 1

        if written_length > 0xf:
            raise RuntimeError(f"Error: Too many items in shop: {written_length}")

        return written_length


class ShopInventoryBuilder(object):
    def __init__(self):
        self._magic = []
        self._armor = []
        self._weapons = []
        self._items = []

    def add_magic(self, magic_id: int) -> ShopInventoryBuilder:
        self._magic.append(magic_id)
        return self

    def add_armor(self, armor_id: int) -> ShopInventoryBuilder:
        self._armor.append(armor_id)
        return self

    def add_weapon(self, weapon_in: int) -> ShopInventoryBuilder:
        self._weapons.append(weapon_in)
        return self

    def add_item(self, item_id: int) -> ShopInventoryBuilder:
        self._items.append(item_id)
        return self

    def build(self):
        stream = OutputStream()
        written_length = 0
        if len(self._magic) > 0:
            for magic_id in self._magic:
                stream.put_u8(magic_id)
                written_length += 1

        if len(self._armor) > 0:
            stream.put_u8(0xfc)
            for item_id in self._armor:
                stream.put_u8(item_id)
                written_length += 1

        if len(self._weapons) > 0:
            stream.put_u8(0xfd)
            for item_id in self._weapons:
                stream.put_u8(item_id)
                written_length += 1

        if len(self._items) > 0:
            stream.put_u8(0xfe)
            for item_id in self._items:
                stream.put_u8(item_id)
                written_length += 1

        if written_length > 0xf:
            raise RuntimeError(f"Error: Too many items in shop: {written_length}")

        return ShopInventory(InputStream(stream.get_buffer()), written_length)
