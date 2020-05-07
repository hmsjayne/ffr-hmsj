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

from doslib.map import MapHeader, Tile, Npc, Chest, Sprite, Shop, MainData
from doslib.rom import Rom
from stream.inputstream import InputStream
from stream.outputstream import OutputStream


class Maps(object):
    def __init__(self, rom: Rom):
        self._maps = []
        self.dummy_chests = []

        self._map_lut = rom.get_lut(0x1E4F40, 124)
        for map_id, map_addr in enumerate(self._map_lut):
            map_stream = rom.get_stream(Rom.pointer_to_offset(map_addr), bytearray.fromhex("ffff"))
            map_features = MapFeatures(map_id, map_stream)
            self._maps.append(map_features)

            # Collect the dummy chests together
            self.dummy_chests += map_features.dummy_chests

        self.map_extras = []
        map_ptrs = []
        map_extra_stream = rom.open_bytestream(0x2160D0, 0x216770 - 0x2160D0)
        while not map_extra_stream.is_eos():
            exit_data_ptr = map_extra_stream.get_u32()
            music_id = map_extra_stream.get_u16()
            encounter_rate_index = map_extra_stream.get_u16()
            self.map_extras.append(MapExtra(exit_data_ptr, music_id, encounter_rate_index))
            map_ptrs.append(exit_data_ptr)

        ptr_to_map = {}
        for map_id, addr in enumerate(map_ptrs):
            ptr_to_map[addr] = map_id
        sorted_ptrs = sorted(map_ptrs)

        for index in range(1, len(sorted_ptrs) - 1):
            exit_count = int((sorted_ptrs[index + 1] - sorted_ptrs[index]) / 20)
            map_id = ptr_to_map[sorted_ptrs[index]]
            self.map_extras[map_id].exit_count = exit_count

        self.main_data = []
        data_stream = rom.open_bytestream(0x21F274, 0x7b * 32)
        while not data_stream.is_eos():
            self.main_data.append(MainData(data_stream))

    def get_map(self, map_id: int) -> 'MapFeatures':
        return self._maps[map_id]

    def get_map_offset(self, map_id: int) -> int:
        return Rom.pointer_to_offset(self._map_lut[map_id])

    def get_patches(self) -> dict:
        patches = {}

        lut = OutputStream()
        base_addr = self._map_lut[0]
        for index, map_features in enumerate(self._maps):
            # TODO: Figure out what breaks the Caravan.
            if index >= 0x73:
                if base_addr > self._map_lut[index]:
                    raise RuntimeError("Ran out of room in map features!")
                break

            data = OutputStream()
            map_features.write(data)

            # Update the LUT and add this map features data to the patch list.
            lut.put_u32(base_addr)
            patches[Rom.pointer_to_offset(base_addr)] = data.get_buffer()

            # Update the pointer to the next map's features
            base_addr += data.size()

        # Lastly, update the LUT in the patches
        patches[0x1E4F40] = lut.get_buffer()

        # Map extra data
        map_extras = OutputStream()
        for map_extra in self.map_extras:
            map_extras.put_u32(map_extra.exit_data_ptr)
            map_extras.put_u16(map_extra.music_id)
            map_extras.put_u16(map_extra.encounter_rate)
        patches[0x2160D0] = map_extras.get_buffer()

        return patches


class MapFeatures(object):
    def __init__(self, map_id: int, stream: InputStream):
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
                    raise RuntimeError(f"Warning: Map {hex(map_id)} has more than one header?")
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

    def get_event_chest(self, chest_id: int) -> tuple:
        if chest_id >= len(self.chests):
            raise RuntimeError(f"Chest index out of bounds: {chest_id} vs {len(self.chests)}")

        chest = self.chests[chest_id]
        for sprite in self.sprites:
            if chest.x_pos == sprite.x_pos and chest.y_pos == sprite.y_pos:
                return chest, sprite
        raise RuntimeError(f"Chest {chest_id} does not have matching sprite!")

    def find_npc(self, sprite: int) -> int:
        for index, npc in enumerate(self.npcs):
            if npc.sprite_id == sprite:
                return index
        raise RuntimeError(f"Could not fine NPC with sprite {hex(sprite)} in map.")

    def write(self, stream: OutputStream):
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
    def read(stream: InputStream):
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

    def write(self, stream: OutputStream):
        chest_data = (self.id << 24) | (self.item_id << 8) | (self.item_type & 0xff)
        stream.put_u32(chest_data)


class MoneyChest(TreasureChest):
    def __init__(self, chest_data: int):
        self.qty = chest_data & 0xffffff
        self.id = (chest_data >> 24) & 0xff

    def __str__(self):
        return f"{{gil, amount={self.qty}}}"

    def write(self, stream: OutputStream):
        chest_data = (self.id << 24) | self.qty
        stream.put_u32(chest_data)


class MapExtra(object):
    def __init__(self, exit_data_ptr: int, music_id: int, encounter_rate: int):
        self.exit_data_ptr = exit_data_ptr
        self.music_id = music_id
        self.encounter_rate = encounter_rate
        self.exit_count = 0
