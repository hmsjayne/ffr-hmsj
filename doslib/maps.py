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

from doslib.gen.map import MapHeader, Tile, Npc, Chest, Sprite, Shop
from doslib.rom import Rom
from stream.input import Input
from stream.output import Output


class Maps(object):
    def __init__(self, rom: Rom):
        self.maps = []

        self._map_lut = rom.get_lut(0x1E4F40, 124)
        for map_id, map_addr in enumerate(self._map_lut):
            map_stream = rom.get_stream(Rom.pointer_to_offset(map_addr), bytearray.fromhex("ffff"))
            self.maps.append(Map(map_id, map_stream))

    def write(self, rom: Rom) -> Rom:
        lut = Output()
        data = Output()

        next_map_addr = self._map_lut[0]
        data_size = 0
        for map in self.maps:
            lut.put_u32(next_map_addr)
            map.write(data)

            next_map_addr += (data.size() - data_size)
            data_size = data.size()

        patches = {
            0x1E4F40: lut.get_buffer(),
            Rom.pointer_to_offset(self._map_lut[0]): data.get_buffer()
        }
        return rom.apply_patches(patches)


class Map(object):
    def __init__(self, map_id: int, stream: Input):
        self.header = None
        self.tiles = []
        self.npcs = []
        self.chests = []
        self.sprites = []
        self.shops = []

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
