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
from doslib.gen.enemy import Encounter
from doslib.maps import Maps
from doslib.rom import Rom
from doslib.textblock import TextBlock
from ffr.eventrewrite import EventRewriter
from stream.output import Output

KeyItem = namedtuple("KeyItem", ["sprite", "flag", "item", "dialog", "movable"])

NpcSource = namedtuple("NpcLocation", ["map_id", "npc_index", "event_id", "vanilla_ki"])
ChestSource = namedtuple("ChestLocation", ["map_id", "chest_id", "sprite_id", "event_id", "vanilla_ki"])

KEY_ITEMS = {
    "bridge": KeyItem(sprite=0x22, flag=0x03, item=None, dialog=0x127, movable=True),
    "lute": KeyItem(sprite=0x00, flag=0x04, item=0x00, dialog=0x10a, movable=True),
    "ship": KeyItem(sprite=0x45, flag=0x05, item=None, dialog=0x224, movable=True),
    "crown": KeyItem(sprite=0x94, flag=0x06, item=0x01, dialog=0x10b, movable=True),
    "crystal": KeyItem(sprite=0x47, flag=0x07, item=0x02, dialog=0x1f3, movable=True),
    "jolt_tonic": KeyItem(sprite=0x37, flag=0x08, item=0x03, dialog=0x216, movable=True),
    "key": KeyItem(sprite=0x31, flag=0x09, item=0x04, dialog=0x154, movable=False),
    "nitro_powder": KeyItem(sprite=0x0D, flag=0x0A, item=0x05, dialog=0x128, movable=True),
    "canal": KeyItem(sprite=0x00, flag=0x0B, item=None, dialog=0x1e8, movable=True),
    "ruby": KeyItem(sprite=0x58, flag=0x0D, item=0x08, dialog=0x142, movable=False),
    "rod": KeyItem(sprite=0x39, flag=0x0F, item=0x09, dialog=0x21a, movable=True),
    "earth": KeyItem(sprite=0x55, flag=0x11, item=None, dialog=None, movable=True),
    "canoe": KeyItem(sprite=0x38, flag=0x12, item=0x10, dialog=0x1b1, movable=True),
    "fire": KeyItem(sprite=0x56, flag=0x13, item=None, dialog=None, movable=True),
    "levistone": KeyItem(sprite=0x57, flag=0x14, item=0x0a, dialog=0x10c, movable=False),
    "tail": KeyItem(sprite=0x25, flag=0x17, item=0x0c, dialog=0x10d, movable=True),
    "class_change": KeyItem(sprite=0x64, flag=0x18, item=None, dialog=0x1d2, movable=False),
    "bottle": KeyItem(sprite=0x44, flag=0x19, item=0x0e, dialog=None, movable=True),
    "oxyale": KeyItem(sprite=0x29, flag=0x1a, item=0x0f, dialog=0x1c0, movable=True),
    "slab": KeyItem(sprite=0x1B, flag=0x1c, item=0x07, dialog=0x10e, movable=True),
    "water": KeyItem(sprite=0x54, flag=0x1d, item=None, dialog=None, movable=True),
    "lufienish": KeyItem(sprite=0x3A, flag=0x1e, item=None, dialog=0x235, movable=True),
    "chime": KeyItem(sprite=0x21, flag=0x1f, item=0x0b, dialog=0x240, movable=True),
    "cube": KeyItem(sprite=0x2B, flag=0x20, item=0x0d, dialog=0x241, movable=True),
    "adamant": KeyItem(sprite=0x59, flag=0x21, item=0x06, dialog=0x10f, movable=False),
    "air": KeyItem(sprite=0x53, flag=0x22, item=None, dialog=None, movable=True),
    "excalibur": KeyItem(sprite=0x3C, flag=0x23, item=0x11, dialog=0x1ed, movable=True),
    "gear": KeyItem(sprite=0x8F, flag=None, item=None, dialog=None, movable=True),
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

        # Swap the flag the King sets (0x2 to 0x3).
        king_flag = EventBuilder() \
            .add_flag("bridge_built", 0x3) \
            .set_flag("bridge_built", 0x0) \
            .get_event()
        self.rom = self.rom.apply_patch(0xa618, king_flag)

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
                self._replace_map_sprite(source.map_id, source.npc_index, key_item.sprite, key_item.movable)

                # Special case for "Sara" -- also update Chaos Shrine.
                if placement.location == "sara":
                    self._replace_map_sprite(0x1f, 6, key_item.sprite, key_item.movable)
                    self._rewrite_map_init_event(0x1f, 0x1, 0x1, 6)

            if placement.location == "bikke":
                self._better_pirates(placement.item)

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
                replacement.remove_visiting_pose(key_item.movable)

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

    def _replace_map_sprite(self, map_id: int, npc_index: int, sprite: int, movable: bool):
        self.maps._maps[map_id].npcs[npc_index].sprite_id = sprite

        # Some sprites weren't designed to move, so hold them still.
        if not movable:
            self.maps._maps[map_id].npcs[npc_index].move_speed = 0

    def _rewrite_map_init_event(self, map_id: int, vanilla_flag, new_flag, visiting_npcs):
        map_event_ptr = Rom.pointer_to_offset(self.map_events.get_addr(map_id))
        map_event = Event(self.rom.get_event(map_event_ptr))
        replacement = EventRewriter(map_event)

        replacement.replace_chest()
        replacement.replace_conditional(vanilla_flag, new_flag)

        # Dump out any posing in the map init events for visiting NPCs
        if visiting_npcs is not None:
            replacement.visiting_npc(visiting_npcs)
            if map_id == 0x1f:
                replacement.remove_visiting_pose(True)

        map_output = Output()
        replacement.rewrite().write(map_output)
        self.rom = self.rom.apply_patches({map_event_ptr: map_output.get_buffer()})

    def _better_pirates(self, key_item: str):
        if key_item not in BETTER_PIRATES:
            return

        formation_stream = self.rom.open_bytestream(0x2288B4, 0x1CD4)
        formations = []
        while not formation_stream.is_eos():
            formations.append(Encounter(formation_stream))
        pirates = formations[0x7e]

        total_enemy_count = 0
        for index, enemy in enumerate(BETTER_PIRATES[key_item]):
            if enemy.enemy_id != -1:
                pirates.groups[index].enemy_id = enemy.enemy_id
                pirates.groups[index].min_count = enemy.number
                pirates.groups[index].max_count = enemy.number
            total_enemy_count += enemy.number

        if total_enemy_count == 1:
            pirates.config = 0x3
        elif total_enemy_count <= 4:
            pirates.config = 0x02
        else:
            pirates.config = 0x00

        formation_stream = Output()
        for formation in formations:
            formation.write(formation_stream)
        self.rom = self.rom.apply_patch(0x2288B4, formation_stream.get_buffer())

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


MiniFormation = namedtuple("MiniFormation", ["enemy_id", "number"])

# Because there's not enough detail to pick out what the encounter configuration should be based
# only on the data here, there's a bit of rule breaking.
# Encounters are always sized based on the number of enemies in them:
#  - 1: Fiend size :)
#  - 2-4: Large size
#  - 5+: Small
# Don't mix land + flying...
#
# So what do you do if you want 2 small enemies? Add an extra entry with enemy_id=-1 with the number required to
# bump into the correct category. (So 1 large would be the 1 enemy + 1 more -1 enemy.
# See the "crown" item below.
# NOTE: enemy_id=-1 *MUST* be at the end. If they're mixed in the middle BAD THING will happen.
BETTER_PIRATES = {
    "crown": [MiniFormation(enemy_id=0x67, number=4), MiniFormation(enemy_id=-1, number=1)],
    "class_change": [MiniFormation(enemy_id=0x43, number=1), MiniFormation(enemy_id=0x6b, number=1),
                     MiniFormation(enemy_id=0x6a, number=1), MiniFormation(enemy_id=0x42, number=1)],
    "lufienish": [MiniFormation(enemy_id=0x32, number=4)],
}
