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
import copy
import json
from collections import namedtuple
from random import seed, randint
from subprocess import run, PIPE

from doslib.event import EventTable, EventTextBlock, Event
from doslib.eventbuilder import EventBuilder
from doslib.maps import Maps
from doslib.gen.map import Npc
from doslib.rom import Rom
from ffr.eventrewrite import EventRewriter, Reward
from stream.input import Input
from stream.output import Output


# TODO: Remove this once the class based one works
def solve_key_item_placement(seed: int):
    """Create a random distribution for key items (KI).
    Note: this requires an installation of Clingo 4.5 or better
    :param seed: The random number seed to use for the solver.
    :return: A list of tuples that contain item+location for each KI.
    """
    command = [
        "clingo", "asp/KeyItemSolving.lp", "asp/KeyItemData.lp",
        "--sign-def=3",
        "--seed=" + str(seed),
        "--outf=2"
    ]

    clingo_out = json.loads(run(command, stdout=PIPE).stdout)
    pairings = clingo_out['Call'][0]['Witnesses'][0]['Value']

    # All pairings are of the form "pair(item,location)" - need to parse the info
    Placement = namedtuple("Placement", ["item", "location"])

    ki_placement = []
    for pairing in pairings:
        pairing = Placement(*pairing[5:len(pairing) - 1].split(","))
        ki_placement.append(pairing)

    return tuple(ki_placement)

class KeyItemPlacement(object):
    
    def __init__(self, rom: Rom, clingo_seed: int):
        self.rom = rom
        self.maps = Maps(rom)
        self.events = EventTable(rom, 0x7788, 0xbb7, base_event_id=0x1388)
        self.event_text_block = EventTextBlock(rom)
        
        self.item_data = {
            "bridge": ('flag', 0x02),
            "ship": ('flag', 0x05),
            "canal": ('flag', 0x0b),
            "earth": ('flag', 0x11),
            "fire": ('flag', 0x13),
            "water": ('flag', 0x1d),
            "air": ('flag', 0x22),
            "lute": ('item', 0x00),
            "crown": ('item', 0x01),
            "crystal": ('item', 0x02),
            "jolt_tonic": ('item', 0x03),
            "key": ('item', 0x04),
            "nitro_powder": ('item', 0x05),
            "adamant": ('item', 0x06),
            "slab": ('item', 0x07),
            "ruby": ('item', 0x08),
            "rod": ('item', 0x09),
            "levistone": ('item', 0x0a),
            "chime": ('item', 0x0b),
            "tail": ('item', 0x0c),
            "cube": ('item', 0x0d),
            "bottle": ('item', 0x0e),
            "oxyale": ('item', 0x0f),
            "canoe": ('item', 0x10),
            "excalibur": ('item', 0x11),
            "gear": ('item', 0xFF),
        }

        self.item_sprite = {
            "bridge": 0x22,  # King
            "lute": 0x00,  # Princess Sarah
            "ship": 0x45,
            "canal": 0x3B,
            "earth": 0x51,
            "fire": 0x52,
            "water": 0x50,
            "air": 0x4F,
            "crown": 0x94,  # Black Wizard (Black)
            "crystal": 0x47,
            "jolt_tonic": 0x37,
            "key": 0x31,
            "nitro_powder": 0x0D,  # Soldier
            "adamant": 0x59,
            "slab": 0x1B,  # Mermaid
            "ruby": 0x58,  # The Ruby Sprite
            "rod": 0x39,
            "levistone": 0x57,
            "chime": 0x21,
            "tail": 0x25,  # A Bat - any better ideas?
            "cube": 0x2B,  # Sadly, no 0x9S exists
            "bottle": 0x44,
            "oxyale": 0x29,
            "canoe": 0x38,
            "excalibur": 0x3C,
            "gear": 0xFF
        }

        self.location_event_id = {
            "lich": 0x13B3,
            "kary": 0x13A8,
            "kraken": 0x13A3,
            "tiamat": 0x13BB,
            "sara": 0x13A7,
            "king": 0x138B,  # This is also, like, fighting Garland and stuff. It big.
            "bikke": 0x13B5,
            "marsh": 0x1398,
            "locked_cornelia": 0x13AD,
            "nerrick": 0x1393,
            "vampire": 0x13B7,
            "sarda": 0x13B8,
            "ice": 0x139F,
            "caravan": 0xFFFF,
            "astos": 0x1390,
            "matoya": 0x1391,
            "elf": 0x139A,
            "ordeals": 0x13AD,
            "waterfall": 0x13BD,
            "fairy": 0x138F,
            "mermaids": 0x13B4,
            "lefien": 0x1395,
            "smith": 0x139D,
            "lukahn": 0x1394,
            "sky2": 0x138D,
            "desert": 0xFFFF,
        }

        # This one's a *little* hacky - each item of the array is a tuple
        # or 3ple: tuples are other NPCs, and 3ples are chests
        self.location_map_objects = {
            "lich": [(0x05, 10)],
            "kary": [(0x2E, 0)],
            "kraken": [(0x17, 0)],
            "tiamat": [(0x60, 0)],
            "sara": [(0x1F, 6), (0x39, 3)],
            "king": [(0x39, 2)],
            "bikke": [(0x62, 2)],
            "marsh": [(0x5B, 5, 0)],
            "locked_cornelia": [(0x38, 2, 2)],
            "nerrick": [(0x38,9)],
            "vampire": [(0x03, 1, 0)],
            "sarda": [(0x37, 0)],
            "ice": [(0x44, 0)],
            "caravan": [(0x73, 0)],
            "astos": [(0x58, 0)],
            "matoya": [(0x61, 4)],
            "elf": [(0x06, 7)],
            "ordeals": [(0x4F, 8, 0)],
            "waterfall": [(0x53, 0)],
            "fairy": [(0x47, 11)],
            "mermaids": [(0x1E, 12, 0)],
            "lefien": [(0x70, 11)],
            "smith": [(0x57, 4)],
            "lukahn": [(0x2F, 13)],
            "sky2": [(0x5D, 0)],
            "desert": [None]
        }
                             
        self._do_placement(clingo_seed)

    def _solve_placement(self, seed: int) -> tuple:
        """Create a random distribution for key items (KI).

        Note: this requires an installation of Clingo 4.5 or better

        :param seed: The random number seed to use for the solver.
        :return: A list of tuples that contain item+location for each KI.
        """
        command = [
            "clingo", "asp/KeyItemSolving.lp", "asp/KeyItemData.lp",
            "--sign-def=3",
            "--seed=" + str(seed),
            "--outf=2"
        ]

        clingo_out = json.loads(run(command, stdout=PIPE).stdout)
        pairings = clingo_out['Call'][0]['Witnesses'][0]['Value']

        # All pairings are of the form "pair(item,location)" - need to parse the info
        Placement = namedtuple("Placement", ["item", "location"])

        ki_placement = []
        for pairing in pairings:
            pairing = Placement(*pairing[5:len(pairing) - 1].split(","))
            ki_placement.append(pairing)

        return tuple(ki_placement)

    def _do_placement(self, clingo_seed:int):
        key_item_locations = self._solve_placement(clingo_seed)

        # The Key items returned work like this. Suppose a Placement returned was
        # `Placement(item='oxyale', location='king')` this means that the "Oxyale" key item
        # should be found in the King of Cornelia location.
        #
        # This does *NOT* mean the King of Cornelia will give you Oxyale, rather, it means the NPC
        # that gives Oxyale (the Fairy) should be placed in the King's spot.
        #
        # Further, the Fairy in the King of Cornelia's spot, will be there at the start of the game, and
        # won't need to be rescued from the Bottle. It *does* mean that the Fairy won't provide Oxyale
        # until Garland is defeated and that NPC (or treasure) is itself rescued.
        sara_sprite = None
        king_sprite = None
        for placement in key_item_locations:
            print(f"Placement: {placement}")
            self._replace_item_event(self.item_data[placement.item],self.location_event_id[placement.location])
            self._replace_map_sprite(self.item_sprite[placement.item],self.location_map_objects[placement.location])
            if placement.location == "sara":
                sara_sprite = self.item_sprite[placement.item]
            if placement.location == "king":
                king_sprite = self.item_sprite[placement.item]

        self.rom = self._placement_king(king_sprite, sara_sprite)
        self.rom = self.maps.write(self.rom)

    def _replace_item_event(self, item_id:int, event_id:int):
        """Replace the item given in Event event_id with item_id"""
    
    def _replace_map_sprite(self, new_sprite:int, locations_to_edit):
        for loc in locations_to_edit:
            if loc == None:
                """Do nothing"""
            elif len(loc) == 2: #An NPC to replace
                self.maps._maps[loc[0]].npcs[loc[1]].sprite_id = new_sprite
            else: #A chest (w/ event sprite)
                print(len(self.maps._maps[loc[0]].sprites))
                chest = self.maps._maps[loc[0]].chests.pop(loc[1]) #Remove & Return
                sprite = self.maps._maps[loc[0]].sprites.pop(loc[2])
                new_npc = bytearray(b'\x02\x00')
                new_npc.extend(int.to_bytes(sprite.event, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(sprite.x_pos, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(sprite.y_pos, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(new_sprite, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(0x00, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(0x00, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(0x01, 2, byteorder="little", signed=False))
                self.maps._maps[loc[0]].npcs.append(Npc(Input(new_npc)))

    def _placement_king(self, king_sprite_id: int, kidnapped_sprite_id: int) -> Rom:
        garland_event_offset = Rom.pointer_to_offset(self.events.get_addr(0x138B))

        king_event = Event(self.rom.get_event(garland_event_offset))
        replacement = EventRewriter(king_event)
        replacement.include_dialogs(0x131)
        replacement.rewrite_dialog(0x127, 0x10b)

        # NPC indecies are:
        # - 6: Princess Sara's slot
        # - 2: The King of Cornelia
        # - 3: Pricess Sara in the throne room.
        replacement.visiting_npc(6, 2, 3)

        replacement.replace_reward(Reward(flag=0x2, mask=0x0), Reward(item=0x1))

        event_output = Output()
        replacement.rewrite().write(event_output)

        # Princess Sara has a unique sprite pose of her lying down, which is
        # set by the map init routine for the Chaos Shrine (map ID 0x1f).
        # The easy way around this is to change the command to just say "face down/south".
        make_npc_face_south = EventBuilder().set_npc_pose(6, 0).get_event()

        # There are two maps that Princess Sara appears on, and so our replacement
        # has to be placed in both places.
        maps = self.maps
        chaos_shrine = maps.get_map(0x1F)
        cornelia_castle_2f = maps.get_map(0x39)

        # In the Chaos Shrine, Sara is NPC #6
        chaos_shrine.npcs[6].sprite_id = kidnapped_sprite_id
        chaos_shrine_out = Output()
        chaos_shrine.write(chaos_shrine_out)

        # And in Cornelia Castle, she's NPC #3
        cornelia_castle_2f.npcs[3].sprite_id = kidnapped_sprite_id
        # And the King is #2
        cornelia_castle_2f.npcs[2].sprite_id = king_sprite_id
        cornelia_castle_2f_out = Output()
        cornelia_castle_2f.write(cornelia_castle_2f_out)

        patches = {
            0x813c: make_npc_face_south,
            garland_event_offset: event_output.get_buffer(),
            maps.get_map_offset(0x1f): chaos_shrine_out.get_buffer(),
            maps.get_map_offset(0x39): cornelia_castle_2f_out.get_buffer()
        }
        return self.rom.apply_patches(patches)