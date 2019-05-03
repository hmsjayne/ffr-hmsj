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
from event import easm
from event.epp import pparse
from ffr.eventrewrite import EventRewriter
from ffr.keyitemevents import *
from stream.outputstream import OutputStream, AddressableOutputStream

KeyItem = namedtuple("KeyItem", ["sprite", "flag", "item", "dialog", "movable"])

NpcSource = namedtuple("NpcLocation", ["map_id", "npc_index", "event_id", "vanilla_ki"])
ChestSource = namedtuple("ChestLocation", ["map_id", "chest_id", "sprite_id", "event_id", "vanilla_ki"])

NewKeyItem = namedtuple("NewKeyItem", ["sprite", "reward", "dialog", "movable"])
NewNpcSource = namedtuple("NewNpcSource", ["map_id", "npc_index", "event_id", "event", "map_init"])
NewChestSource = namedtuple("NewChestSource", ["map_id", "chest_id", "sprite_id", "event_id", "event", "map_init"])

KEY_ITEMS = {
    "bridge": KeyItem(sprite=0x22, flag=0x03, item=None, dialog=0x127, movable=True),
    "lute": KeyItem(sprite=0x00, flag=0x04, item=0x00, dialog=0x10a, movable=True),
    "ship": KeyItem(sprite=0x45, flag=0x05, item=None, dialog=0x224, movable=True),
    "crown": KeyItem(sprite=0x94, flag=0x06, item=0x01, dialog=0x10b, movable=True),
    "crystal": KeyItem(sprite=0x47, flag=0x07, item=0x02, dialog=0x1f3, movable=True),
    "jolt_tonic": KeyItem(sprite=0x37, flag=0x08, item=0x03, dialog=0x216, movable=True),
    "key": KeyItem(sprite=0x31, flag=0x09, item=0x04, dialog=0x154, movable=False),
    "nitro_powder": KeyItem(sprite=0x0D, flag=0x0A, item=0x05, dialog=0x128, movable=True),
    "canal": KeyItem(sprite=0x3B, flag=0x0B, item=None, dialog=0x1e8, movable=True),
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

NEW_REWARD_SOURCE = {
    "king": NewNpcSource(map_id=0x39, npc_index=2, event_id=0x138B, event=king_event, map_init=None),
    "sara": NewNpcSource(map_id=0x39, npc_index=3, event_id=0x13A7, event=sara_event,
                         map_init=cornelia_castle_2f_event),
    "bikke": NewNpcSource(map_id=0x62, npc_index=2, event_id=0x13B5, event=bikke_event,
                          map_init=pravoka_init_event),
    "marsh": NewChestSource(map_id=0x5B, chest_id=5, sprite_id=0, event_id=0x1398, event=marsh_event,
                            map_init=marsh_cave_b3_init),
    "locked_cornelia": NewChestSource(map_id=0x38, chest_id=2, sprite_id=2, event_id=0x13ad,
                                      event=locked_cornelia_event, map_init=cornelia_castle_1f_event),
    "nerrick": NewNpcSource(map_id=0x57, npc_index=11, event_id=0x1393, event=nerrik_event, map_init=mt_duergar_init),
}

NEW_KEY_ITEMS = {
    "bridge": NewKeyItem(sprite=0x22, reward=bridge_reward, dialog=0x127, movable=True),
    "lute": NewKeyItem(sprite=0x00, reward=lute_reward, dialog=0x10a, movable=True),
    "ship": NewKeyItem(sprite=0x45, reward=ship_reward, dialog=0x224, movable=True),
    "crown": NewKeyItem(sprite=0x94, reward=crown_reward, dialog=0x10b, movable=True),
    "crystal": NewKeyItem(sprite=0x47, reward=crystal_reward, dialog=0x1f3, movable=True),
    "jolt_tonic": NewKeyItem(sprite=0x37, reward=jolt_tonic_reward, dialog=0x216, movable=True),
    "key": NewKeyItem(sprite=0x31, reward=key_reward, dialog=0x154, movable=False),
    "nitro_powder": NewKeyItem(sprite=0x0D, reward=nitro_powder_reward, dialog=0x128, movable=True),
    "canal": NewKeyItem(sprite=0x3B, reward=canal_reward, dialog=0x1e8, movable=True),
    "ruby": NewKeyItem(sprite=0x58, reward=ruby_reward, dialog=0x142, movable=False),
    "rod": NewKeyItem(sprite=0x39, reward=rod_reward, dialog=0x21a, movable=True),
    "canoe": NewKeyItem(sprite=0x38, reward=canoe_reward, dialog=0x1b1, movable=True),
    "levistone": NewKeyItem(sprite=0x57, reward=levistone_reward, dialog=0x10c, movable=False),
    "tail": NewKeyItem(sprite=0x25, reward=tail_reward, dialog=0x10d, movable=True),
    "class_change": NewKeyItem(sprite=0x64, reward=class_change_reward, dialog=0x1d2, movable=False),
    "bottle": NewKeyItem(sprite=0x44, reward=bottle_reward, dialog=None, movable=True),
    "oxyale": NewKeyItem(sprite=0x29, reward=oxyale_reward, dialog=0x1c0, movable=True),
    "slab": NewKeyItem(sprite=0x1B, reward=slab_reward, dialog=0x10e, movable=True),
    "lufienish": NewKeyItem(sprite=0x3A, reward=lufienish_reward, dialog=0x235, movable=True),
    "chime": NewKeyItem(sprite=0x21, reward=chime_reward, dialog=0x240, movable=True),
    "cube": NewKeyItem(sprite=0x2B, reward=cube_reward, dialog=0x241, movable=True),
    "adamant": NewKeyItem(sprite=0x59, reward=adamant_reward, dialog=0x10f, movable=False),
    "excalibur": NewKeyItem(sprite=0x3C, reward=excalibur_reward, dialog=0x1ed, movable=True),
}


class KeyItemPlacement(object):

    def __init__(self, rom: Rom, clingo_seed: int):
        self.rom = rom
        self.maps = Maps(rom)
        self.events = EventTable(rom, 0x7788, 0xbb7, base_event_id=0x1388)
        self.map_events = EventTable(rom, 0x7050, 0xD3, base_event_id=0x0)
        self.event_text_block = EventTextBlock(rom)

        self.our_events = AddressableOutputStream(0x8223F4C, max_size=0x1860)

        self._do_placement(clingo_seed)

    def _do_placement(self, clingo_seed: int):
        key_item_locations = self._solve_placement(clingo_seed)

        for placement in key_item_locations:

            if placement.location not in NEW_REWARD_SOURCE:
                continue
            if placement.item not in NEW_KEY_ITEMS:
                continue

            print(f"Placement: {placement}")

            source = NEW_REWARD_SOURCE[placement.location]
            key_item = NEW_KEY_ITEMS[placement.item]

            event_addr = self.events.get_addr(source.event_id)
            event_source = pparse(f"{key_item.reward}\n\n{source.event}")
            event = easm.parse(event_source, event_addr)
            self.rom = self.rom.apply_patch(Rom.pointer_to_offset(event_addr), event)

            if source.map_init is not None:
                map_event_addr = self.our_events.current_addr()

                map_event_source = pparse(f"{key_item.reward}\n\n{source.map_init}")
                map_event = easm.parse(map_event_source, map_event_addr)

                self.map_events.set_addr(source.map_id, map_event_addr)
                self.our_events.put_bytes(map_event)

            if isinstance(source, NewNpcSource):
                self._replace_map_npc(source.map_id, source.npc_index, key_item.sprite, key_item.movable)

                # Special case for "Sara" -- also update Chaos Shrine.
                if placement.location == "sara":
                    self._replace_map_npc(0x1f, 6, key_item.sprite, key_item.movable)

        # Write out our (moved) rewritten events along with the updated
        # LUTs for them.
        self.rom = self.rom.apply_patches({
            0x7050: self.map_events.get_lut(),
            0x7788: self.events.get_lut(),
            0x223F4C: self.our_events.get_buffer()
        })

        self._unite_mystic_key_doors()
        self._rewrite_give_texts()
        self.rom = self.maps.write(self.rom)

    def _unite_mystic_key_doors(self):
        maps_with_doors = [
            0x06,  # Elven Castle
            0x38,  # Castle Cornelia 1F
        ]

        # There are two events (in vanilla) for mystic key locked doors.
        # - 0x1f4a: This door has been bound by the mystic key.
        # - 0x23cd: The treasure house has been bound by the mystic key.
        # In order to simplify some of the logic, change the 3 instances of the second to the first
        # since it's more generic.
        for map_id in maps_with_doors:
            for sprite in self.maps._maps[map_id].sprites:
                if sprite.event == 0x23cd:
                    sprite.event = 0x1f4a

    def _rewrite_give_texts(self):
        self.event_text_block.strings[0x127] = TextBlock.encode_text("You obtain the bridge.\x00")
        self.event_text_block.strings[0x1e8] = TextBlock.encode_text("You obtain the canal.\x00")
        self.event_text_block.strings[0x1d2] = TextBlock.encode_text("You obtain class change.\x00")
        self.event_text_block.strings[0x1bf] = TextBlock.encode_text("You obtain a bottle.\x00")
        self.event_text_block.strings[0x235] = TextBlock.encode_text("You can now speak Lufenian.\x00")
        self.rom = self.event_text_block.pack(self.rom)

    def _replace_map_npc(self, map_id: int, npc_index: int, sprite: int, movable: bool):
        self.maps._maps[map_id].npcs[npc_index].sprite_id = sprite

        # Some sprites weren't designed to move, so hold them still.
        if not movable:
            self.maps._maps[map_id].npcs[npc_index].move_speed = 0

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
