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

from doslib.gen.map import MapHeader, Tile, Npc, Chest, Sprite, Shop
from doslib.rom import Rom
from stream.input import Input
from stream.output import Output


class Maps(object):
    def __init__(self, rom: Rom):
        self._maps = []
        self.dummy_chests = []

        self._map_lut = rom.get_lut(0x1E4F40, 124)
        for map_id, map_addr in enumerate(self._map_lut):
            map_stream = rom.get_stream(Rom.pointer_to_offset(map_addr), bytearray.fromhex("ffff"))
            map = Map(map_id, map_stream)
            self._maps.append(map)

            # Collect the dummy chests together
            self.dummy_chests += map.dummy_chests

    def get_map(self, map_id: int) -> Map:
        return self._maps[map_id]

    def get_map_offset(self, map_id: int) -> int:
        return Rom.pointer_to_offset(self._map_lut[map_id])

    def write(self, rom: Rom) -> Rom:
        # lut = Output()
        # data = Output()

        # next_map_addr = self._map_lut[0]
        patches = {}
        # data_size = 0
        for index, map in enumerate(self._maps):
            data = Output()
            # lut.put_u32(next_map_addr)
            map.write(data)

            patches[self._map_lut[index]] = data.get_buffer()

            # next_map_addr += (data.size() - data_size)
            # data_size = data.size()

        # patches = {
        #     0x1E4F40: lut.get_buffer(),
        #     Rom.pointer_to_offset(self._map_lut[0]): data.get_buffer()
        # }
        return rom.apply_patches(patches)


class Map(object):
    def __init__(self, map_id: int, stream: Input):
        self.header = None
        self.tiles = []
        self.npcs = []
        self.chests = []
        self.sprites = []
        self.shops = []
        self.dummy_chests = []

        data_type = stream.peek_u16()
        while data_type != 0xffff:
            if data_type == 0x0:

                if self.header is not None:
                    print(f"Warning: Map {hex(map_id)} has more than one header?")
                self.header = MapHeader(stream)
            elif data_type == 0x1:
                self.tiles.append(Tile(stream))
            elif data_type == 0x2:
                self.npcs.append(Npc(stream))
            elif data_type == 0x3:
                self.chests.append(Chest(stream))
            elif data_type == 0x4:
                self.sprites.append(Sprite(stream))
            elif data_type == 0x5:
                self.shops.append(Shop(stream))
            else:
                raise RuntimeError(f"Unknown type: {data_type}")

            data_type = stream.peek_u16()

        # Some treasure chests are basically placeholders for events. We want to
        # make a note of these chest IDs.
        if len(self.chests) > 0 and len(self.sprites) > 0:
            for index, chest in enumerate(self.chests):
                for sprite in self.sprites:
                    if chest.x_pos == sprite.x_pos and chest.y_pos == sprite.y_pos:
                        self.dummy_chests.append(chest.chest_id)
                        break

    def write(self, stream: Output):
        self.header.write(stream)

        for tile in self.tiles:
            tile.write(stream)
        for npc in self.npcs:
            npc.write(stream)
        for chest in self.chests:
            chest.write(stream)
        for sprite in self.sprites:
            sprite.write(stream)
        for shop in self.shops:
            shop.write(stream)

        # Close the map at the end. :)
        stream.put_u16(0xffff)


class TreasureChest(object):
    @staticmethod
    def read(stream: Input):
        chest_data = stream.get_u32()
        if chest_data & 0x80000000 == 0:
            return MoneyChest(chest_data)
        else:
            return ItemChest(chest_data)


class ItemChest(TreasureChest):
    def __init__(self, chest_data: int):
        self.item_type = chest_data & 0xff
        self.item_id = (chest_data >> 8) & 0xffff
        self.id = (chest_data >> 24) & 0xff

    def __str__(self):
        return f"{{item, type={self.item_type}, id={hex(self.item_id)}}}"

    def write(self, stream: Output):
        chest_data = (self.id << 24) | (self.item_id << 8) | (self.item_type & 0xff)
        stream.put_u32(chest_data)


class MoneyChest(TreasureChest):
    def __init__(self, chest_data: int):
        self.qty = chest_data & 0xffffff
        self.id = (chest_data >> 24) & 0xff

    def __str__(self):
        return f"{{gil, amount={self.qty}}}"

    def write(self, stream: Output):
        chest_data = (self.id << 24) | self.qty
        stream.put_u32(chest_data)