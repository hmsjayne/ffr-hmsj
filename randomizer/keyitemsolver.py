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

from doslib.event import EventTable, EventTextBlock
from doslib.gen.map import Npc
from doslib.maps import Maps, TreasureChest
from doslib.rom import Rom
from doslib.textblock import TextBlock
from event import easm
from event.epp import pparse
from randomizer.keyitemevents import *
from stream.outputstream import AddressableOutputStream, OutputStream

KeyItem = namedtuple("KeyItem", ["sprite", "movable", "key_item", "reward"])
NpcSource = namedtuple("NpcSource", ["map_id", "npc_index", "event_id", "event", "map_init"])
ChestSource = namedtuple("ChestSource", ["map_id", "chest_id", "sprite_id", "event_id", "event", "map_init"])

EVENT_SOURCE_MAP = {
    0x03: earth_b3_init,
    0x39: cornelia_castle_2f_init,
    0x62: pravoka_init,
    0x5B: marsh_cave_b3_init,
    0x58: nw_keep_init,
    0x61: matoyas_cave_init,
    0x06: elven_castle_init,
    0x38: cornelia_castle_1f_event,
    0x37: sages_cave_init,
    0x2F: crescent_lake_init,
    0x44: ice_b3_init,
    0x4D: citadel_of_trials_f1_init,
    0x4F: citadel_of_trials_f3_init,
    0x54: bahamuts_cave_init,
    0x53: waterfall_init,
    0x47: gaia_init,
    0x1E: mermaid_floor_init,
    0x6A: melmond_init,
    0x70: lefein_init,
    0x5D: sky_f2_init,
    0x57: mt_duergar_init,
    0x138B: king_event,
    0x13A7: sara_event,
    0x13B5: bikke_event,
    0x1398: marsh_event,
    0x1390: astos_event,
    0x1391: matoya_event,
    0x139A: elf_prince_event,
    0x13ad: locked_cornelia_event,
    0x1393: nerrik_event,
    0x13B7: vampire_event,
    0x13b8: sarda_event,
    0x1394: lukahn_event,
    0x139F: levistone_event,
    0x13AA: citadel_of_trials_chest_event,
    0x1396: bahamuts_cave_event,
    0x13BD: waterfall_robot_event,
    0x138F: fairy_event,
    0x13B4: slab_chest_event,
    0x13A5: dr_unne_event,
    0x1395: lefein_event,
    0x138D: sky2_adamantite_event,
    0x139D: smyth_event,

    # Extra events
    0x139c: better_earth_plate
}

NEW_REWARD_SOURCE = {
    "king": NpcSource(map_id=0x39, npc_index=2, event_id=0x138B, event=king_event, map_init=None),
    "sara": NpcSource(map_id=0x39, npc_index=3, event_id=0x13A7, event=sara_event, map_init=cornelia_castle_2f_init),
    "bikke": NpcSource(map_id=0x62, npc_index=2, event_id=0x13B5, event=bikke_event, map_init=pravoka_init),
    "marsh": ChestSource(map_id=0x5B, chest_id=5, sprite_id=0, event_id=0x1398, event=marsh_event,
                         map_init=marsh_cave_b3_init),
    "astos": NpcSource(map_id=0x58, npc_index=0, event_id=0x1390, event=astos_event, map_init=nw_keep_init),
    "matoya": NpcSource(map_id=0x61, npc_index=4, event_id=0x1391, event=matoya_event, map_init=matoyas_cave_init),
    "elf": NpcSource(map_id=0x06, npc_index=7, event_id=0x139A, event=elf_prince_event, map_init=elven_castle_init),
    "locked_cornelia": ChestSource(map_id=0x38, chest_id=2, sprite_id=2, event_id=0x13ad, event=locked_cornelia_event,
                                   map_init=cornelia_castle_1f_event),
    "nerrick": NpcSource(map_id=0x57, npc_index=11, event_id=0x1393, event=nerrik_event, map_init=mt_duergar_init),
    "vampire": ChestSource(map_id=0x03, chest_id=1, sprite_id=0, event_id=0x13B7, event=vampire_event,
                           map_init=earth_b3_init),
    "sarda": NpcSource(map_id=0x37, npc_index=0, event_id=0x13b8, event=sarda_event, map_init=sages_cave_init),
    "lukahn": NpcSource(map_id=0x2F, npc_index=13, event_id=0x1394, event=lukahn_event, map_init=crescent_lake_init),
    "ice": NpcSource(map_id=0x44, npc_index=0, event_id=0x139F, event=levistone_event, map_init=ice_b3_init),
    "citadel_of_trials": ChestSource(map_id=0x4F, chest_id=8, sprite_id=0, event_id=0x13AA,
                                     event=citadel_of_trials_chest_event, map_init=citadel_of_trials_f1_init),
    "bahamut": NpcSource(map_id=0x54, npc_index=2, event_id=0x1396, event=bahamuts_cave_event,
                         map_init=bahamuts_cave_init),
    "waterfall": NpcSource(map_id=0x53, npc_index=0, event_id=0x13BD, event=waterfall_robot_event,
                           map_init=waterfall_init),
    "fairy": NpcSource(map_id=0x47, npc_index=11, event_id=0x138F, event=fairy_event, map_init=gaia_init),
    "mermaids": ChestSource(map_id=0x1E, chest_id=12, sprite_id=0, event_id=0x13B4, event=slab_chest_event,
                            map_init=mermaid_floor_init),
    "dr_unne": NpcSource(map_id=0x6A, npc_index=0, event_id=0x13A5, event=dr_unne_event, map_init=melmond_init),
    "lefien": NpcSource(map_id=0x70, npc_index=11, event_id=0x1395, event=lefein_event, map_init=lefein_init),
    "sky2": NpcSource(map_id=0x5D, npc_index=0, event_id=0x138D, event=sky2_adamantite_event, map_init=sky_f2_init),
    "smyth": NpcSource(map_id=0x57, npc_index=4, event_id=0x139D, event=smyth_event, map_init=mt_duergar_init),
}

NEW_KEY_ITEMS = {
    "bridge": KeyItem(sprite=0x22, movable=True, key_item=None, reward=bridge_reward),
    "lute": KeyItem(sprite=0x00, movable=True, key_item=0x00, reward=lute_reward),
    "ship": KeyItem(sprite=0x45, movable=True, key_item=None, reward=ship_reward),
    "crown": KeyItem(sprite=0x94, movable=True, key_item=0x01, reward=crown_reward),
    "crystal": KeyItem(sprite=0x47, movable=True, key_item=0x02, reward=crystal_reward),
    "jolt_tonic": KeyItem(sprite=0x37, movable=True, key_item=0x03, reward=jolt_tonic_reward),
    "mystic_key": KeyItem(sprite=0x31, movable=False, key_item=0x04, reward=mystic_key_reward),
    "nitro_powder": KeyItem(sprite=0x0D, movable=True, key_item=0x05, reward=nitro_powder_reward),
    "canal": KeyItem(sprite=0x3B, movable=True, key_item=None, reward=canal_reward),
    "star_ruby": KeyItem(sprite=0x58, movable=False, key_item=0x08, reward=star_ruby_reward),
    "rod": KeyItem(sprite=0x39, movable=True, key_item=0x09, reward=rod_reward),
    "canoe": KeyItem(sprite=0x38, movable=True, key_item=0x10, reward=canoe_reward),
    "levistone": KeyItem(sprite=0x57, movable=False, key_item=0x0a, reward=levistone_reward),
    "rats_tail": KeyItem(sprite=0x25, movable=True, key_item=0x0c, reward=rats_tail_reward),
    "promotion": KeyItem(sprite=0x64, movable=False, key_item=None, reward=promotion_reward),
    "bottle": KeyItem(sprite=0x44, movable=True, key_item=0x0e, reward=bottle_reward),
    "oxyale": KeyItem(sprite=0x29, movable=True, key_item=0x0f, reward=oxyale_reward),
    "rosetta_stone": KeyItem(sprite=0x1B, movable=True, key_item=0x07, reward=rosetta_stone_reward),
    "lufienish": KeyItem(sprite=0x3A, movable=True, key_item=None, reward=lufienish_reward),
    "chime": KeyItem(sprite=0x21, movable=True, key_item=0x0b, reward=chime_reward),
    "warp_cube": KeyItem(sprite=0x2B, movable=True, key_item=0x0d, reward=warp_cube_reward),
    "adamantite": KeyItem(sprite=0x59, movable=False, key_item=0x06, reward=adamantite_reward),
    "excalibur": KeyItem(sprite=0x3C, movable=True, key_item=0x11, reward=excalibur_reward),
}


class KeyItemPlacement(object):

    def __init__(self, rom: Rom, clingo_seed: int):
        self.rom = rom
        self.maps = Maps(rom)
        self.events = EventTable(rom, 0x7788, 0x44, base_event_id=0x1388)
        self.map_events = EventTable(rom, 0x7050, 0xD3, base_event_id=0x0)
        self.event_text_block = EventTextBlock(rom)

        self.chests = self._load_chests()
        self.our_events = AddressableOutputStream(0x8223F4C, max_size=0x1860)

        self._do_placement(clingo_seed)

    def _do_placement(self, clingo_seed: int):
        key_item_locations = self._solve_placement(clingo_seed)
        source_headers = self._prepare_header(key_item_locations)

        for event_id, source in EVENT_SOURCE_MAP.items():
            if event_id < 0xff or event_id in [0x139c]:
                use_our_event = True
            else:
                use_our_event = False

            if use_our_event:
                event_addr = self.our_events.current_addr()

                if event_id < 0xff:
                    self.map_events.set_addr(event_id, event_addr)
                else:
                    self.events.set_addr(event_id, event_addr)
            else:
                event_addr = self.events.get_addr(event_id)

            event_source = pparse(f"{source_headers}\n\n{source}")
            event = easm.parse(event_source, event_addr)

            if use_our_event:
                self.our_events.put_bytes(event)
            else:
                self.rom = self.rom.apply_patch(Rom.pointer_to_offset(event_addr), event)

        self._update_npcs(key_item_locations)
        self._unite_mystic_key_doors()
        self._better_earth_plate()
        self._rewrite_give_texts()
        self._save_chests()

        # Write out our (moved) rewritten events along with the updated
        # LUTs for them.
        self.rom = self.rom.apply_patches({
            0x7050: self.map_events.get_lut(),
            0x7788: self.events.get_lut(),
            0x223F4C: self.our_events.get_buffer()
        })
        self.rom = self.maps.write(self.rom)

    def _prepare_header(self, key_item_locations: tuple) -> str:
        working_header = ""

        for placement in key_item_locations:
            if placement.location not in NEW_REWARD_SOURCE:
                continue
            if placement.item not in NEW_KEY_ITEMS:
                continue

            location = placement.location
            key_item = NEW_KEY_ITEMS[placement.item]

            base_reward_text = key_item.reward
            reward_text = base_reward_text.replace("GIVE_REWARD", f"GIVE_{location.upper()}_REWARD")
            reward_text = reward_text.replace("%text_id", f"%{location}_text_id")
            reward_text = reward_text.replace("%reward_flag", f"%{location}_reward_flag")
            working_header += f";---\n; {placement.item} -> {location}\n;---\n{reward_text}\n\n"
        return working_header

    def _update_npcs(self, key_item_locations: tuple):

        for placement in key_item_locations:

            if placement.location not in NEW_REWARD_SOURCE:
                continue
            if placement.item not in NEW_KEY_ITEMS:
                continue

            print(f"Placement: {placement}")

            source = NEW_REWARD_SOURCE[placement.location]
            key_item = NEW_KEY_ITEMS[placement.item]
            if isinstance(source, NpcSource):
                self._replace_map_npc(source.map_id, source.npc_index, key_item.sprite, key_item.movable)

                # Special case for "Sara" -- also update Chaos Shrine.
                if placement.location == "sara":
                    self._replace_map_npc(0x1f, 6, key_item.sprite, key_item.movable)
            elif isinstance(source, ChestSource):
                self._replace_chest(source.map_id, source.chest_id, key_item.key_item)

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

    def _better_earth_plate(self):
        self.maps._maps[0x3].npcs[0xe].event = 0x139c

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

    def _replace_chest(self, map_id: int, chest_id: int, key_item:int):
        safe_key_item = {
            0x38: NEW_KEY_ITEMS["mystic_key"].key_item,
            0x4F: NEW_KEY_ITEMS["crown"].key_item,
            0x1E: NEW_KEY_ITEMS["oxyale"].key_item,
        }

        map = self.maps.get_map(map_id)
        chest, sprite = map.get_event_chest(chest_id)
        if key_item is None:
            key_item = safe_key_item[map_id]
            print(f"None key item for {hex(map_id)} -> {hex(key_item)}")
        self.chests[chest.chest_id].item_id = (key_item + 1)

    def _load_chests(self) -> list:
        chest_stream = self.rom.open_bytestream(0x217FB4, 0x400)
        chests = []
        for index in range(256):
            chest = TreasureChest.read(chest_stream)
            chests.append(chest)
        return chests

    def _save_chests(self):
        # Save the chests (without key items in them).
        chest_data = OutputStream()
        for chest in self.chests:
            chest.write(chest_data)
        self.rom = self.rom.apply_patch(0x217FB4, chest_data.get_buffer())

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
