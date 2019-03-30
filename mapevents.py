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

'''Data Structure for Map Edits
    We'll read in a bunch of data from an input stream, then spit it back out reordered as a test'''

from struct import unpack, pack

from doslib.map import NPC, Chest, Tile, Shop, Sprite, MapHeader

class MapEvents(object):
    '''Lotsa data to dump here; we'll get into that '''
    def __init__(self, rom):
        MAP_DATA_PTR = 0x1E54A4
        VANILLA_MAP_COUNT = 0x7B #We're going to avoid the DoS maps for now
        
        maps = []