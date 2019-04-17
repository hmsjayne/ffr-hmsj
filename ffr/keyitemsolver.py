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
import json
from collections import namedtuple
from subprocess import run, PIPE

from doslib.event import EventTable, EventTextBlock, Event
from doslib.eventbuilder import EventBuilder
from doslib.gen.map import Npc
from doslib.maps import Maps
from doslib.rom import Rom
from ffr.eventrewrite import EventRewriter
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
        self.map_events = EventTable(rom, 0x7050, 0xD3, base_event_id=0x0)
        self.event_text_block = EventTextBlock(rom)

        self.flag_index = {
            "bridge": 0x03,
            "lute": 0x04,
            "ship": 0x05,
            "crown": 0x06,
            "crystal": 0x07,
            "jolt_tonic": 0x08,
            "key": 0x09,
            "nitro_powder": 0x0A,
            "canal": 0x0B,
            "ruby": 0x0D,
            "rod": 0x0F,
            "earth": 0x11,
            "canoe": 0x12,
            "fire": 0x13,
            "levistone": 0x14,
            "tail": 0x17,
            "class_change": 0x18,
            "oxyale": 0x1a,
            "slab": 0x1c,
            "water": 0x1d,
            "lufienish": 0x1e,
            "chime": 0x1f,
            "cube": 0x20,
            "adamant": 0x21,
            "air": 0x22,
            "excalibur": 0x23
        }

        self.item_index = {
            "lute": 0x00,
            "crown": 0x01,
            "crystal": 0x02,
            "jolt_tonic": 0x03,
            "key": 0x04,
            "nitro_powder": 0x05,
            "adamant": 0x06,
            "slab": 0x07,
            "ruby": 0x08,
            "rod": 0x09,
            "levistone": 0x0a,
            "chime": 0x0b,
            "tail": 0x0c,
            "cube": 0x0d,
            "bottle": 0x0e,
            "oxyale": 0x0f,
            "canoe": 0x10,
            "excalibur": 0x11,
            "gear": 0xFF,
        }

        self.item_data = {
            "bridge": ('flag', 0x03),
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

        self.vanilla_flags = {
            "king": 0x02,
            "sara": 0x04,
            "bikke": 0x05,
            "marsh": 0x06,
            "astos": 0x07,
            "matoya": 0x08,
            "elf": 0x09,
            "locked_cornelia": 0x0A,
            "nerrick": 0x0B,
            "vampire": 0x0D,
            "sarda": 0x0F,
            "lich": 0x11,
            "lukahn": 0x12,
            "kary": 0x13,
            "ice": 0x14,
            "ordeals": 0x17,
            "bahamut": 0x18,
            "fairy": 0x1a,
            "mermaids": 0x1c,
            "kraken": 0x1d,
            "unne": 0x1e,
            "lefien": 0x1f,
            "waterfall": 0x20,
            "sky2": 0x21,
            "tiamat": 0x22,
            "smith": 0x23
        }

        self.vanilla_rewards = {
            "lich": ('flag', 0x11),
            "kary": ('flag', 0x13),
            "kraken": ('flag', 0x1d),
            "tiamat": ('flag', 0x22),
            "sara": ('item', 0x00),
            "king": ('flag', 0x02),
            "bikke": ('flag', 0x05),
            "marsh": ('item', 0x01),
            "locked_cornelia": ('item', 0x05),
            "nerrick": ('flag', 0x0b),
            "vampire": ('item', 0x08),
            "sarda": ('item', 0x09),
            "ice": ('item', 0x0a),
            "caravan": ('item', 0x0e),
            "astos": ('item', 0x02),
            "matoya": ('item', 0x03),
            "elf": ('item', 0x04),
            "ordeals": ('item', 0x0c),
            "waterfall": ('item', 0x0d),
            "fairy": ('item', 0x0f),
            "mermaids": ('item', 0x07),
            "lefien": ('item', 0x0b),
            "smith": ('item', 0x11),
            "lukahn": ('item', 0x10),
            "sky2": ('item', 0x06),
            "desert": ('item', 0xFF),
        }
        # -------
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

        self.map_check_index = {
            "lich": 0x05,
            "kary": 0x2E,
            "kraken": 0x17,
            "tiamat": 0x60,
            "sara": 0x39,
            "king": 0x39,
            "bikke": 0x62,
            "marsh": 0x5B,
            "locked_cornelia": 0x38,
            "nerrick": 0x57,
            "vampire": 0x03,
            "sarda": 0x37,
            "ice": 0x44,
            "caravan": 0x73,
            "astos": 0x58,
            "matoya": 0x61,
            "elf": 0x06,
            "ordeals": 0x4F,
            "waterfall": 0x53,
            "fairy": 0x47,
            "mermaids": 0x1E,
            "lefien": 0x70,
            "smith": 0x57,
            "lukahn": 0x2F,
            "sky2": 0x5D
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
            "nerrick": [(0x57, 11)],
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

        self.vanilla_dialog_keys = {
            "king": 0x127,
            "sara": 0x10a,
            "bikke": 0x224,
            "marsh": 0x10b,
            "astos": 0x1f3,
            "matoya": 0x216,
            "elf": 0x154,
            "locked_cornelia": 0x128,
            "nerrick": 0x1e8,
            "vampire": 0x142,
            "sarda": 0x21a,
            "lich": -1,
            "lukahn": 0x1b1,
            "kary": -1,
            "ice": 0x10c,
            "ordeals": 0x10d,
            "bahamut": 0x1d2,
            "fairy": 0x1c0,
            "mermaids": 0x10e,
            "kraken": -1,
            "unne": 0x235,
            "lefien": 0x240,
            "waterfall": 0x241,
            "sky2": 0x10f,
            "tiamat": -1,
            "smith": 0x1ed
        }

        self.dialog_keys = {
            "bridge": 0x127,
            "lute": 0x10a,
            "ship": 0x224,
            "crown": 0x10b,
            "crystal": 0x1f3,
            "jolt_tonic": 0x216,
            "key": 0x154,
            "nitro_powder": 0x128,
            "canal": 0x1e8,
            "ruby": 0x142,
            "rod": 0x21a,
            "earth": -1,
            "canoe": 0x1b1,
            "fire": -1,
            "levistone": 0x10c,
            "tail": 0x10d,
            "class_change": 0x1d2,
            "oxyale": 0x1c0,
            "slab": 0x10e,
            "water": -1,
            "lufienish": 0x235,
            "chime": 0x240,
            "cube": 0x241,
            "adamant": 0x10f,
            "air": -1,
            "excalibur": 0x1ed
        }

        self._do_placement(clingo_seed)

    def _idx_to_array(self, x: int):
        lil = x % 0x100
        big = (x - lil) / 0x100
        return [lil, big]

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

    def _do_placement(self, clingo_seed: int):
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
        new_events = dict()
        for placement in key_item_locations:
            print(f"Placement: {placement}")
            self._replace_item_event(placement.item, placement.location)
            self._replace_map_sprite(self.item_sprite[placement.item], self.location_map_objects[placement.location])
            if placement.location == "sara":
                sara_sprite = self.item_sprite[placement.item]
            if placement.location == "king":
                king_sprite = self.item_sprite[placement.item]

        self.rom = self._placement_king(king_sprite, sara_sprite)
        self._remove_bridge_trigger()
        self.rom = self.maps.write(self.rom)

    def _remove_bridge_trigger(self):
        tiles = self.maps._maps[0x38].tiles
        for tile in tiles:
            if tile.event == 0x1392:
                # Remove the bridge building cut-scene trigger.
                tile.event = 0x0

    def _replace_item_event(self, item: str, location: str):
        """So, we take in the item and the location of said item"""
        """And take our time calling up the needed data here"""
        """In particular, there's two events that need to be fixed:"""
        """One is indexed the same as the map, and needs to look at """
        map_id = None
        event_id = None
        if location in self.map_check_index:
            map_id = self.map_check_index[location]
        if location in self.location_event_id:
            event_id = self.location_event_id[location]

        if item == "bottle" or location == "desert":
            return

        if map_id is not None:
            # print(map_id)
            map_event_ptr = Rom.pointer_to_offset(self.map_events.get_addr(map_id))
            map_event = Event(self.rom.get_event(map_event_ptr))
            replacement = EventRewriter(map_event)

            old_item_flag = self.vanilla_flags[location]
            new_item_flag = self.flag_index[item]

            replacement.replace_chest()
            replacement.replace_conditional(old_item_flag, new_item_flag)

            map_output = Output()
            replacement.rewrite().write(map_output)
            self.rom = self.rom.apply_patches({map_event_ptr: map_output.get_buffer()})
        if event_id is not None:
            event_ptr = Rom.pointer_to_offset(self.events.get_addr(event_id))
            event = Event(self.rom.get_event(event_ptr))
            replacement = EventRewriter(event)

            item_id = self.item_data[item]
            replacement.replace_flag(self.vanilla_flags[location], self.flag_index[item])

            if item_id[0] != 'flag':
                replacement.give_item(item_id[1])

            old_dialog = self.vanilla_dialog_keys[location]
            new_dialog = self.dialog_keys[item]

            if old_dialog != -1 and new_dialog != -1:
                replacement.rewrite_dialog(old_dialog, new_dialog)

            event_output = Output()
            replacement.rewrite().write(event_output)
            self.rom = self.rom.apply_patches({event_ptr: event_output.get_buffer()})

    def _replace_map_sprite(self, new_sprite: int, locations_to_edit):
        for loc in locations_to_edit:
            if loc is None:
                """Do nothing"""
            elif len(loc) == 2:  # An NPC to replace
                self.maps._maps[loc[0]].npcs[loc[1]].sprite_id = new_sprite
            """else:  # A chest (w/ event sprite)
                print(len(self.maps._maps[loc[0]].sprites))
                chest = self.maps._maps[loc[0]].chests.pop(loc[1])  # Remove & Return
                sprite = self.maps._maps[loc[0]].sprites.pop(loc[2])
                new_npc = bytearray(b'\x02\x00')
                new_npc.extend(int.to_bytes(sprite.event, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(sprite.x_pos, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(sprite.y_pos, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(new_sprite, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(0x00, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(0x00, 2, byteorder="little", signed=False))
                new_npc.extend(int.to_bytes(0x01, 2, byteorder="little", signed=False))
                self.maps._maps[loc[0]].npcs.append(Npc(Input(new_npc)))"""

    def _placement_king(self, king_sprite_id: int, kidnapped_sprite_id: int) -> Rom:
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
            maps.get_map_offset(0x1f): chaos_shrine_out.get_buffer(),
            maps.get_map_offset(0x39): cornelia_castle_2f_out.get_buffer()
        }
        return self.rom.apply_patches(patches)
