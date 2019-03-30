#!/usr/bin/env python3

#  Copyright 2019 Stella Mazeika
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

# Designed to parse the Map data in a human reable format.
# Takes in a FF DoS rom named 'FF1.gba' because lazy
import sys

from doslib.rom import Rom

if sys.argv[1] is not None:
    rom = Rom(sys.argv[1])
else:
    rom = Rom('./primary_code/FF1.gba')

locations = ''
temp_spirtes = ''
with open("labels/locations.txt", "r") as f:
    locations = f.readlines()
with open("labels/sprites.txt", "r") as f:
    temp_sprites = f.readlines()

sprites = dict()

for s in temp_sprites:
    index = int(s.split(' ')[0], 16)
    sprites[index] = s.split(' ')[1].strip() + ' (' + s.split(' ')[0].strip() + ')'


class Map_Events:
    def __init__(self, name, ptr):
        self.name = name
        self.pointer = ptr
        self.boundaries = []
        self.chests = []
        self.interactive_sprites = []
        self.special_tiles = []
        self.NPCs = []
        self.shops = []

    # Takes in an array of 10 bytes
    def add_boundaries(self, data):
        self.boundaries = [(data[2], data[6]), (data[4], data[8])]

    def add_chest(self, data, cur_ptr):
        new_chest = dict()
        new_chest['x_coord'] = data[4]
        new_chest['y_coord'] = data[6]
        new_chest['chest_id'] = data[2]
        new_chest['ptr'] = cur_ptr
        self.chests.append(new_chest)

    def add_tile(self, data, cur_ptr):
        new_tile = dict()
        new_tile['x_coord'] = data[4]
        new_tile['y_coord'] = data[6]
        new_tile['event'] = data[2:4]
        new_tile['ptr'] = cur_ptr
        self.special_tiles.append(new_tile)

    def add_NPC(self, data, cur_ptr):
        new_NPC = dict()
        new_NPC['event'] = data[2:4]
        new_NPC['x_coord'] = data[4]
        new_NPC['y_coord'] = data[6]
        new_NPC['x_coord'] = data[4]
        new_NPC['Sprite'] = sprites[data[8]]
        new_NPC['move_speed'] = data[10]
        new_NPC['init_facing'] = data[12]
        new_NPC['in_room'] = data[14]
        new_NPC['ptr'] = cur_ptr
        self.NPCs.append(new_NPC)

    def add_sprite(self, data, cur_ptr):
        new_sprite = dict()
        new_sprite['x_coord'] = data[4]
        new_sprite['y_coord'] = data[6]
        new_sprite['event'] = data[2:4]
        new_sprite['ptr'] = cur_ptr
        self.interactive_sprites.append(new_sprite)

    def add_shops(self, data, cur_ptr):
        new_shop = dict()
        new_shop['x_coord'] = data[4]
        new_shop['y_coord'] = data[6]
        new_shop['event'] = data[2:4]
        new_shop['ptr'] = cur_ptr
        self.shops.append(new_shop)

    def writeMap(self, file):
        file.write("Current Map: " + self.name)
        file.write("Starts at " + hex(self.pointer) + "\n\n")
        file.write("Chest Count: " + str(len(self.chests)) + "\n")
        for c in self.chests:
            file.write(hex(c['ptr']) + " = Chest ID " + str(c['chest_id']) + " at (" + str(c['x_coord']) + "," + str(
                c['y_coord']) + ")\n")
        file.write("\nNPC Count: " + str(len(self.NPCs)) + "\n")
        for c in self.NPCs:
            file.write(
                hex(c['ptr']) + " = NPC " + str(c['Sprite']) + " with event ID 0x" + c['event'].hex() + " at (" + str(
                    c['x_coord']) + "," + str(c['y_coord']) + ")\n")
        file.write("\nTile Count: " + str(len(self.special_tiles)) + "\n")
        for c in self.special_tiles:
            file.write(
                hex(c['ptr']) + " = Tile with event ID 0x" + c['event'].hex() + " at (" + str(c['x_coord']) + "," + str(
                    c['y_coord']) + ")\n")
        file.write("\nSprite Count: " + str(len(self.interactive_sprites)) + "\n")
        for c in self.interactive_sprites:
            file.write(hex(c['ptr']) + " = Sprite 0x" + c['event'].hex() + " at (" + str(c['x_coord']) + "," + str(
                c['y_coord']) + ") \n")
        file.write("\n")


MAP_DATA_PTR = 0x1E54A4
cur_ptr = MAP_DATA_PTR
map_index = 0
map_count = len(locations)

maps = []

while (map_index < map_count):
    cur_map = Map_Events(locations[map_index], cur_ptr)
    maps.append(cur_map)
    cur_map.add_boundaries(rom.rom_data[cur_ptr:cur_ptr + 10])
    cur_ptr += 10
    while (rom.rom_data[cur_ptr:cur_ptr + 2] != b'\xFF\xFF'):
        # print(rom.rom_data[cur_ptr])
        if (rom.rom_data[cur_ptr] == 0x01):
            # Special Tile
            cur_map.add_tile(rom.rom_data[cur_ptr:cur_ptr + 8], cur_ptr)
            cur_ptr += 8
        elif (rom.rom_data[cur_ptr] == 0x02):
            # NPC
            cur_map.add_NPC(rom.rom_data[cur_ptr:cur_ptr + 16], cur_ptr)
            cur_ptr += 16
        elif (rom.rom_data[cur_ptr] == 0x03):
            # Chest
            cur_map.add_chest(rom.rom_data[cur_ptr:cur_ptr + 8], cur_ptr)
            cur_ptr += 8
        elif (rom.rom_data[cur_ptr] == 0x04):
            # Interactable Sprite
            cur_map.add_sprite(rom.rom_data[cur_ptr:cur_ptr + 8], cur_ptr)
            cur_ptr += 8
        elif (rom.rom_data[cur_ptr] == 0x05):
            # Shop
            cur_map.add_shops(rom.rom_data[cur_ptr:cur_ptr + 8], cur_ptr)
            cur_ptr += 8
    map_index += 1
    cur_ptr += 2

# Great, now I need to print it out :/

with open("map_events.txt", "w") as f:
    for m in maps:
        m.writeMap(f)
