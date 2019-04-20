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
from doslib.maps import Maps
from doslib.rom import Rom
from doslib.textblock import TextBlock
from ffr.eventrewrite import EventRewriter
from stream.output import Output

KeyItem = namedtuple("KeyItem", ["sprite", "flag", "item", "dialog"])

NpcSource = namedtuple("NpcLocation", ["map_id", "npc_index", "event_id", "vanilla_ki"])
ChestSource = namedtuple("ChestLocation", ["map_id", "chest_id", "sprite_id", "event_id", "vanilla_ki"])

KEY_ITEMS = {
    "bridge": KeyItem(sprite=0x22, flag=0x03, item=None, dialog=0x127),
    "lute": KeyItem(sprite=0x00, flag=0x04, item=0x00, dialog=0x10a),
    "ship": KeyItem(sprite=0x45, flag=0x05, item=None, dialog=0x224),
    "crown": KeyItem(sprite=0x94, flag=0x06, item=0x01, dialog=0x10b),
    "crystal": KeyItem(sprite=0x47, flag=0x07, item=0x02, dialog=0x1f3),
    "jolt_tonic": KeyItem(sprite=0x37, flag=0x08, item=0x03, dialog=0x216),
    "key": KeyItem(sprite=0x31, flag=0x09, item=0x04, dialog=0x154),
    "nitro_powder": KeyItem(sprite=0x0D, flag=0x0A, item=0x05, dialog=0x128),
    "canal": KeyItem(sprite=0x00, flag=0x0B, item=None, dialog=0x1e8),
    "ruby": KeyItem(sprite=0x58, flag=0x0D, item=0x08, dialog=0x142),
    "rod": KeyItem(sprite=0x39, flag=0x0F, item=0x09, dialog=0x21a),
    "earth": KeyItem(sprite=0x00, flag=0x11, item=None, dialog=None),
    "canoe": KeyItem(sprite=0x38, flag=0x12, item=0x10, dialog=0x1b1),
    "fire": KeyItem(sprite=0x00, flag=0x13, item=None, dialog=None),
    "levistone": KeyItem(sprite=0x57, flag=0x14, item=0x0a, dialog=0x10c),
    "tail": KeyItem(sprite=0x25, flag=0x17, item=0x0c, dialog=0x10d),
    "class_change": KeyItem(sprite=0x64, flag=0x18, item=None, dialog=0x1d2),
    "bottle": KeyItem(sprite=0x44, flag=0x19, item=0x0e, dialog=None),
    "oxyale": KeyItem(sprite=0x29, flag=0x1a, item=0x0f, dialog=0x1c0),
    "slab": KeyItem(sprite=0x1B, flag=0x1c, item=0x07, dialog=0x10e),
    "water": KeyItem(sprite=0x00, flag=0x1d, item=None, dialog=None),
    "lufienish": KeyItem(sprite=0x3A, flag=0x1e, item=None, dialog=0x235),
    "chime": KeyItem(sprite=0x21, flag=0x1f, item=0x0b, dialog=0x240),
    "cube": KeyItem(sprite=0x2B, flag=0x20, item=0x0d, dialog=0x241),
    "adamant": KeyItem(sprite=0x59, flag=0x21, item=0x06, dialog=0x10f),
    "air": KeyItem(sprite=0x00, flag=0x22, item=None, dialog=None),
    "excalibur": KeyItem(sprite=0x3C, flag=0x23, item=0x11, dialog=0x1ed),
    "gear": KeyItem(sprite=0x8F, flag=None, item=None, dialog=None),
}

REWARD_SOURCE = {
    "lich": NpcSource(map_id=0x05, npc_index=10, event_id=0x13B3, vanilla_ki="earth"),
    "kary": NpcSource(map_id=0x2E, npc_index=0, event_id=0x13A8, vanilla_ki="fire"),
    "kraken": NpcSource(map_id=0x17, npc_index=0, event_id=0x13A3, vanilla_ki="water"),
    "tiamat": NpcSource(map_id=0x60, npc_index=0, event_id=0x13BB, vanilla_ki="air"),
    "sara": NpcSource(map_id=0x39, npc_index=3, event_id=0x13A7, vanilla_ki="lute"),
    "king": NpcSource(map_id=0x39, npc_index=2, event_id=0x138B, vanilla_ki="bridge"),
    "bikke": NpcSource(map_id=0x62, npc_index=2, event_id=0x13B5, vanilla_ki="ship"),
    "marsh": ChestSource(map_id=0x5B, chest_id=5, sprite_id=0, event_id=0x1398, vanilla_ki="crown"),
    "locked_cornelia": ChestSource(map_id=0x38, chest_id=2, sprite_id=2, event_id=0x13AD, vanilla_ki="nitro_powder"),
    "nerrick": NpcSource(map_id=0x57, npc_index=11, event_id=0x1393, vanilla_ki="canal"),
    "vampire": ChestSource(map_id=0x03, chest_id=1, sprite_id=0, event_id=0x13B7, vanilla_ki="ruby"),
    "sarda": NpcSource(map_id=0x37, npc_index=0, event_id=0x13B8, vanilla_ki="rod"),
    "ice": NpcSource(map_id=0x44, npc_index=0, event_id=0x139F, vanilla_ki="levistone"),
    "caravan": NpcSource(map_id=0x73, npc_index=0, event_id=None, vanilla_ki="bottle"),
    "astos": NpcSource(map_id=0x58, npc_index=0, event_id=0x1390, vanilla_ki="crystal"),
    "matoya": NpcSource(map_id=0x61, npc_index=4, event_id=0x1391, vanilla_ki="jolt_tonic"),
    "elf": NpcSource(map_id=0x06, npc_index=7, event_id=0x139A, vanilla_ki="key"),
    "ordeals": ChestSource(map_id=0x4F, chest_id=8, sprite_id=0, event_id=0x13AA, vanilla_ki="tail"),
    "bahamut": NpcSource(map_id=0x54, npc_index=2, event_id=0x1396, vanilla_ki="class_change"),
    "waterfall": NpcSource(map_id=0x53, npc_index=0, event_id=0x13BD, vanilla_ki="cube"),
    "fairy": NpcSource(map_id=0x47, npc_index=11, event_id=0x138F, vanilla_ki="oxyale"),
    "mermaids": ChestSource(map_id=0x1E, chest_id=12, sprite_id=0, event_id=0x13B4, vanilla_ki="slab"),
    "dr_unne": NpcSource(map_id=0x6A, npc_index=0, event_id=0x13A5, vanilla_ki="lufienish"),
    "lefien": NpcSource(map_id=0x70, npc_index=11, event_id=0x1395, vanilla_ki="chime"),
    "smith": NpcSource(map_id=0x57, npc_index=4, event_id=0x139D, vanilla_ki="excalibur"),
    "lukahn": NpcSource(map_id=0x2F, npc_index=13, event_id=0x1394, vanilla_ki="canoe"),
    "sky2": NpcSource(map_id=0x5D, npc_index=0, event_id=0x138D, vanilla_ki="adamant"),
    "desert": None,
}


class KeyItemPlacement(object):

    def __init__(self, rom: Rom, clingo_seed: int):
        self.rom = rom
        self.maps = Maps(rom)
        self.events = EventTable(rom, 0x7788, 0xbb7, base_event_id=0x1388)
        self.map_events = EventTable(rom, 0x7050, 0xD3, base_event_id=0x0)
        self.event_text_block = EventTextBlock(rom)
        self._do_placement(clingo_seed)

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

        for placement in key_item_locations:
            print(f"Placement: {placement}")

            # TODO: Add logic to allow another item in the shop at the very least. :)
            if placement.item == "bottle" or placement.location == "desert":
                continue

            source = REWARD_SOURCE[placement.location]
            key_item = KEY_ITEMS[placement.item]

            self._replace_item_event(source, key_item)

            if isinstance(source, NpcSource):
                self.maps._maps[source.map_id].npcs[source.npc_index].sprite_id = key_item.sprite

                # Special case for "Sara" -- also update Chaos Shrine.
                if placement.location == "sara":
                    self.maps._maps[0x1f].npcs[6].sprite_id = key_item.sprite
                    self._rewrite_map_init_event(0x1f, 0x1, 0x1, 6)

        self._remove_bridge_trigger()
        self._shorten_canal_scene()
        self._rewrite_give_texts()

        self.rom = self.maps.write(self.rom)

    def _remove_bridge_trigger(self):
        tiles = self.maps._maps[0x38].tiles
        for tile in tiles:
            if tile.event == 0x1392:
                # Remove the bridge building cut-scene trigger.
                tile.event = 0x0

    def _shorten_canal_scene(self):
        # This cuts out the part of the scene that switches to the
        # overworld and shows the rocks collapsing, but keeps the
        # rest of it.
        event = EventBuilder() \
            .add_label("end_up_collaps", 0x800c238) \
            .jump_to("end_up_collaps") \
            .get_event()
        self.rom = self.rom.apply_patch(0xc0f4, event)

    def _rewrite_give_texts(self):
        self.event_text_block.strings[0x127] = TextBlock.encode_text("You obtain the bridge.\\x00")
        self.event_text_block.strings[0x1e8] = TextBlock.encode_text("You obtain the canal.\\x00")
        self.event_text_block.strings[0x1d2] = TextBlock.encode_text("You obtain class change.\\x00")
        self.event_text_block.strings[0x235] = TextBlock.encode_text("You can now speak Lufenian.\\x00")
        self.rom = self.event_text_block.pack(self.rom)

    def _replace_item_event(self, source, key_item: KeyItem):
        """So, we take in the item and the location of said item"""
        """And take our time calling up the needed data here"""
        """In particular, there's two events that need to be fixed:"""
        """One is indexed the same as the map, and needs to look at """

        vanilla_item = KEY_ITEMS[source.vanilla_ki]

        if source.map_id is not None:
            # Dump out any posing in the map init events for visiting NPCs
            if isinstance(source, NpcSource):
                visiting_npcs = source.npc_index
            else:
                visiting_npcs = None
            self._rewrite_map_init_event(source.map_id, vanilla_item.flag, key_item.flag, visiting_npcs)

        if source.event_id is not None:
            event_ptr = Rom.pointer_to_offset(self.events.get_addr(source.event_id))
            event = Event(self.rom.get_event(event_ptr))
            replacement = EventRewriter(event)

            replacement.replace_flag(vanilla_item.flag, key_item.flag)

            if key_item.item is not None:
                replacement.give_item(key_item.item)

            if isinstance(source, NpcSource):
                replacement.visiting_npc(source.npc_index)

            # Special case for Sara in event 0x138b - confronting Garland.
            if source.event_id == 0x138b:
                replacement.visiting_npc(6)

            old_dialog = vanilla_item.dialog
            new_dialog = key_item.dialog

            if old_dialog is not None and new_dialog is not None:
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

    def _rewrite_map_init_event(self, map_id: int, vanilla_flag, new_flag, visiting_npcs):
        map_event_ptr = Rom.pointer_to_offset(self.map_events.get_addr(map_id))
        map_event = Event(self.rom.get_event(map_event_ptr))
        replacement = EventRewriter(map_event)

        replacement.replace_chest()
        replacement.replace_conditional(vanilla_flag, new_flag)

        # Dump out any posing in the map init events for visiting NPCs
        if visiting_npcs is not None:
            replacement.visiting_npc(visiting_npcs)

        map_output = Output()
        replacement.rewrite().write(map_output)
        self.rom = self.rom.apply_patches({map_event_ptr: map_output.get_buffer()})

    @staticmethod
    def _solve_placement(seed: int) -> tuple:
        """Create a random distribution for key items (KI).

        Note: this requires an installation of Clingo 4.5 or better

        :param seed: The random number seed to use for the solver.
        :return: A list of tuples that contain item+location for each KI.
        """
        command = [
            "clingo", "asp/KeyItemSolving.lp", "asp/KeyItemData.lp",
            "--sign-def=rnd",
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
