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

from doslib.event import EventTextBlock, EventTables
from doslib.gen.map import Npc
from doslib.maps import Maps, TreasureChest
from doslib.rom import Rom
from doslib.textblock import TextBlock
from event import easm
from event.epp import pparse
from randomizer.keyitemevents import *
from stream.outputstream import AddressableOutputStream, OutputStream

KeyItem = namedtuple("KeyItem", ["sprite", "movable", "key_item", "reward"])
NpcSource = namedtuple("NpcSource", ["map_id", "npc_index"])
ChestSource = namedtuple("ChestSource", ["map_id", "chest_id", "sprite_id"])
VehiclePosition = namedtuple("VehiclePosition", ["x", "y"])

EVENT_SOURCE_MAP = {
    0x00: world_map_init,
    0x03: earth_b3_init,
    0x05: earth_b5_init,
    0x06: elven_castle_init,
    0x17: suken_shrine_1f,
    0x1E: mermaid_floor_init,
    0x1F: chaos_shrine_init,
    0x22: chaos_temple_3f_init,
    0x2e: volcano_b5_init,
    0x2F: crescent_lake_init,
    0x37: sages_cave_init,
    0x38: cornelia_castle_1f_event,
    0x39: cornelia_castle_2f_init,
    0x3A: cornelia_map_init,
    0x44: ice_b3_init,
    0x47: gaia_init,
    0x4D: citadel_of_trials_f1_init,
    0x4F: citadel_of_trials_f3_init,
    0x53: waterfall_init,
    0x54: bahamuts_cave_init,
    0x57: mt_duergar_init,
    0x58: nw_keep_init,
    0x5B: marsh_cave_b3_init,
    0x5D: sky_f2_init,
    0x61: matoyas_cave_init,
    0x62: pravoka_init,
    0x6A: melmond_init,
    0x70: lefein_init,
    0x138B: king_event,
    0x138D: sky2_adamantite_event,
    0x138E: desert_event,
    0x138F: fairy_event,
    0x1390: astos_event,
    0x1391: matoya_event,
    0x1393: nerrik_event,
    0x1394: lukahn_event,
    0x1395: lefein_event,
    0x1396: bahamuts_cave_event,
    0x1398: marsh_event,
    0x139A: elf_prince_event,
    0x139c: better_earth_plate,
    0x139D: smyth_event,
    0x139F: levistone_event,
    0x13A5: dr_unne_event,
    0x13A7: sara_event,
    0x13AA: citadel_of_trials_chest_event,
    0x13ad: locked_cornelia_event,
    0x13af: citadel_guide,
    0x13B4: slab_chest_event,
    0x13B5: bikke_event,
    0x13B7: vampire_event,
    0x13b8: sarda_event,
    0x13BD: waterfall_robot_event,
    0x1f60: wow_chancellor,
    0x13a3: kraken_event,
    0x13a8: kary_event,
    0x13b3: lich_event,

    0x1F49: teleport
}

NEW_REWARD_SOURCE = {
    "king": NpcSource(map_id=0x39, npc_index=2),
    "sara": NpcSource(map_id=0x39, npc_index=3),
    "bikke": NpcSource(map_id=0x62, npc_index=2),
    "marsh": ChestSource(map_id=0x5B, chest_id=5, sprite_id=0),
    "astos": NpcSource(map_id=0x58, npc_index=0),
    "matoya": NpcSource(map_id=0x61, npc_index=4),
    "elf": NpcSource(map_id=0x06, npc_index=7),
    "locked_cornelia": ChestSource(map_id=0x38, chest_id=2, sprite_id=2),
    "nerrick": NpcSource(map_id=0x57, npc_index=11),
    "vampire": ChestSource(map_id=0x03, chest_id=1, sprite_id=0),
    "sarda": NpcSource(map_id=0x37, npc_index=0),
    "lukahn": NpcSource(map_id=0x2F, npc_index=13),
    "ice": NpcSource(map_id=0x44, npc_index=0),
    "citadel_of_trials": ChestSource(map_id=0x4F, chest_id=8, sprite_id=0),
    "bahamut": NpcSource(map_id=0x54, npc_index=2),
    "waterfall": NpcSource(map_id=0x53, npc_index=0),
    "fairy": NpcSource(map_id=0x47, npc_index=11),
    "mermaids": ChestSource(map_id=0x1E, chest_id=12, sprite_id=0),
    "dr_unne": NpcSource(map_id=0x6A, npc_index=0),
    "lefien": NpcSource(map_id=0x70, npc_index=11),
    "sky2": NpcSource(map_id=0x5D, npc_index=0),
    "smyth": NpcSource(map_id=0x57, npc_index=4),
    "desert": ChestSource(map_id=None, chest_id=12, sprite_id=0),
    "lich": NpcSource(map_id=0x05, npc_index=10),
    "kary": NpcSource(map_id=0x2E, npc_index=0),
    "kraken": NpcSource(map_id=0x17, npc_index=0),
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
    "airship": KeyItem(sprite=0xac, movable=False, key_item=None, reward=airship_reward),
    "gear": KeyItem(sprite=0xc7, movable=False, key_item=None, reward=gear_reward),
    "earth": KeyItem(sprite=0x51, movable=False, key_item=None, reward=earth_reward),
    "fire": KeyItem(sprite=0x52, movable=False, key_item=None, reward=fire_reward),
    "water": KeyItem(sprite=0x50, movable=False, key_item=None, reward=water_reward),
}

SHIP_LOCATIONS = {
    "king": VehiclePosition(x=0x918, y=0xa28),
    "sara": VehiclePosition(x=0x918, y=0xa28),
    "bikke": VehiclePosition(x=0xcb8, y=0x928),
    "marsh": VehiclePosition(x=-1, y=-1),
    "astos": VehiclePosition(x=-1, y=-1),
    "matoya": VehiclePosition(x=0x988, y=0x858),
    "elf": VehiclePosition(x=-1, y=-1),
    "locked_cornelia": VehiclePosition(x=0x918, y=0xa28),
    "nerrick": VehiclePosition(x=0x738, y=0x838),
    "vampire": VehiclePosition(x=-1, y=-1),
    "sarda": VehiclePosition(x=-1, y=-1),
    "lukahn": VehiclePosition(x=-1, y=-1),
    "ice": VehiclePosition(x=0xcb8, y=0x928),
    "citadel_of_trials": VehiclePosition(x=-1, y=-1),
    "bahamut": VehiclePosition(x=-1, y=-1),
    "waterfall": VehiclePosition(x=-1, y=-1),
    "fairy": VehiclePosition(x=-1, y=-1),
    "mermaids": VehiclePosition(x=-1, y=-1),
    "dr_unne": VehiclePosition(x=-1, y=-1),
    "lefien": VehiclePosition(x=-1, y=-1),
    "sky2": VehiclePosition(x=-1, y=-1),
    "smyth": VehiclePosition(x=0x738, y=0x838),
    "desert": VehiclePosition(x=-1, y=-1),
    "lich": VehiclePosition(x=-1, y=-1),
    "kary": VehiclePosition(x=-1, y=-1),
    "kraken": VehiclePosition(x=-1, y=-1),
}

AIRSHIP_LOCATIONS = {
    "king": VehiclePosition(x=0x918, y=0x998),
    "sara": VehiclePosition(x=0x918, y=0x998),
    "bikke": VehiclePosition(x=0xcb8, y=0x8f8),
    "marsh": VehiclePosition(x=0x5f8, y=0xe48),
    "astos": VehiclePosition(x=0x5f8, y=0x838),
    "matoya": VehiclePosition(x=0xa18, y=0x6f8),
    "elf": VehiclePosition(x=0x818, y=0xd78),
    "locked_cornelia": VehiclePosition(x=0x918, y=0x998),
    "nerrick": VehiclePosition(x=0x5d8, y=0x958),
    "vampire": VehiclePosition(x=0x3a8, y=0xb48),
    "sarda": VehiclePosition(x=0x178, y=0xb88),
    "lukahn": VehiclePosition(x=0xd38, y=0xd38),
    "ice": VehiclePosition(x=0xc08, y=0xb18),
    "citadel_of_trials": VehiclePosition(x=0x7a8, y=0x278),
    "bahamut": VehiclePosition(x=-1, y=-1),
    "waterfall": VehiclePosition(x=-1, y=-1),
    "fairy": VehiclePosition(x=-1, y=-1),
    "mermaids": VehiclePosition(x=-1, y=-1),
    "dr_unne": VehiclePosition(x=0x4a8, y=0x998),
    "lefien": VehiclePosition(x=-1, y=-1),
    "sky2": VehiclePosition(x=-1, y=-1),
    "smyth": VehiclePosition(x=0x5d8, y=0x958),
    "desert": VehiclePosition(x=0xd68, y=0xe68),
    "lich": VehiclePosition(x=0x3a8, y=0xb48),
    "kary": VehiclePosition(x=0xb68, y=0xc68),
    "kraken": VehiclePosition(x=-1, y=-1),
}

# All pairings are of the form "pair(item,location)" - need to parse the info
Placement = namedtuple("Placement", ["item", "location"])


class KeyItemPlacement(object):

    def __init__(self, rom: Rom, clingo_seed: int = None):
        self.rom = rom
        self.maps = Maps(rom)
        self.events = EventTables(rom)
        self.event_text_block = EventTextBlock(rom)

        self.chests = self._load_chests()
        self.our_events = AddressableOutputStream(0x8223F4C, max_size=0x1860)

        if clingo_seed is not None:
            key_item_locations = self._solve_placement(clingo_seed)
        else:
            key_item_locations = self._vanilla_placement()
        self._do_placement(key_item_locations)

    def _do_placement(self, key_item_locations: tuple):
        source_headers = self._prepare_header(key_item_locations)

        patches = {}
        for event_id, source in EVENT_SOURCE_MAP.items():
            event_source = pparse(f"{source_headers}\n\n{source}")

            event_addr = self.events.get_addr(event_id)
            event_space = self.rom.get_event(Rom.pointer_to_offset(event_addr)).size()

            # See if the event fits into it's vanilla location.
            event = easm.parse(event_source, event_addr)
            if len(event) > event_space:
                # Didn't fit. Move it to our space.
                event_addr = self.our_events.current_addr()
                self.events.set_addr(event_id, event_addr)

                # We'll write all of our events together at the end
                event = easm.parse(event_source, event_addr)
                self.our_events.put_bytes(event)
            else:
                # Add the event to the vanilla patches.
                patches[Rom.pointer_to_offset(event_addr)] = event

        self._update_npcs(key_item_locations)
        self._unite_mystic_key_doors()
        self._better_earth_plate()
        self._rewrite_give_texts()
        self._save_chests()

        # Append our new (relocated) events in the patch data.
        patches[0x223F4C] = self.our_events.get_buffer()

        # And then get all the patch data for the LUTs
        for offset, patch in self.events.get_patches().items():
            patches[offset] = patch
        self.rom = self.rom.apply_patches(patches)
        self.rom = self.maps.write(self.rom)

        # And, finally, update the vehicle start positions based on where they were

        ship_location = None
        airship_location = None
        for placement in key_item_locations:
            if placement.item == "ship":
                ship_location = SHIP_LOCATIONS[placement.location]
                if ship_location.x == -1 or ship_location.y == -1:
                    ship_location = SHIP_LOCATIONS["king"]
                    print(f"Ship placed at {placement.location} -> moved to Cornelia")
                else:
                    print(f"Ship placed: {ship_location}")
            elif placement.item == "airship":
                airship_location = AIRSHIP_LOCATIONS[placement.location]
                if airship_location.x == -1 or airship_location.y == -1:
                    raise RuntimeError(f"Airship placed in an impossible spot? {airship_location}")
                else:
                    print(f"Airship placed: {airship_location}")

        if ship_location is None:
            ship_location = SHIP_LOCATIONS["king"]

        vehicle_starts = OutputStream()
        vehicle_starts.put_u32(ship_location.x)
        vehicle_starts.put_u32(ship_location.y)
        vehicle_starts.put_u32(airship_location.x)
        vehicle_starts.put_u32(airship_location.y)

        self.rom = self.rom.apply_patch(0x65278, vehicle_starts.get_buffer())

    def _prepare_header(self, key_item_locations: tuple) -> str:
        working_header = STD_HEADER

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

            if placement.location == "desert":
                reward_text += f"\n%desert_reward_sprite {hex(key_item.sprite)}"

            working_header += f";---\n; {placement.item} -> {location}\n;---\n{reward_text}\n\n"
        return working_header

    def _update_npcs(self, key_item_locations: tuple):

        print(f"Key Items: {key_item_locations}")

        for placement in key_item_locations:
            if placement.location not in NEW_REWARD_SOURCE:
                continue
            if placement.item not in NEW_KEY_ITEMS:
                continue

            source = NEW_REWARD_SOURCE[placement.location]
            key_item = NEW_KEY_ITEMS[placement.item]
            if isinstance(source, NpcSource):
                self._replace_map_npc(source.map_id, source.npc_index, key_item.sprite, key_item.movable)

                # Special case for "Sara" -- also update Chaos Shrine.
                if placement.location == "sara":
                    self._replace_map_npc(0x1f, 6, key_item.sprite, key_item.movable)
            elif isinstance(source, ChestSource):
                if source.map_id is not None:
                    self._replace_chest(source.map_id, source.chest_id, key_item.sprite)

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
            map = self.maps.get_map(map_id)
            for sprite in map.sprites:
                if sprite.event == 0x23cd:
                    sprite.event = 0x1f4a

    def _better_earth_plate(self):
        self.maps.get_map(0x3).npcs[0xe].event = 0x139c

    def _rewrite_give_texts(self):
        with open("data/event_text.tsv", "r") as event_text:
            for line in event_text.readlines():
                string_num, text = line.strip().split('\t')
                string_num = int(string_num, 16)

                if not text.endswith('\x00'):
                    text += '\x00'

                self.event_text_block.strings[string_num] = TextBlock.encode_text(text)

        self.rom = self.event_text_block.pack(self.rom)

    def _replace_map_npc(self, map_id: int, npc_index: int, sprite: int, movable: bool):
        map = self.maps.get_map(map_id)
        map.npcs[npc_index].sprite_id = sprite

        # Some sprites weren't designed to move, so hold them still.
        if not movable:
            map.npcs[npc_index].move_speed = 0

    def _replace_chest(self, map_id: int, chest_id: int, sprite_id: int):
        map = self.maps.get_map(map_id)
        chest, sprite = map.get_event_chest(chest_id)
        map.chests.remove(chest)
        map.sprites.remove(sprite)

        chest_npc = Npc()
        chest_npc.identifier = 0x2
        chest_npc.in_room = 0x1
        chest_npc.x_pos = sprite.x_pos
        chest_npc.y_pos = sprite.y_pos
        chest_npc.move_speed = 0
        chest_npc.event = sprite.event

        if map_id in [0x38, 0x5b, 0x1e]:
            # Use a chest in Cornelia, Marsh, and the mermaid floor in Sea.
            chest_npc.sprite_id = 0xc7
        else:
            chest_npc.sprite_id = sprite_id
        map.npcs.append(chest_npc)

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
            "clingo", "asp/KeyItemSolvingShip.lp", "asp/KeyItemDataShip.lp",
            "--sign-def=rnd",
            "--seed=" + str(seed),
            "--outf=2"
        ]

        clingo_out = json.loads(run(command, stdout=PIPE).stdout)
        pairings = clingo_out['Call'][0]['Witnesses'][0]['Value']

        ki_placement = []
        for pairing in pairings:
            pairing = Placement(*pairing[5:len(pairing) - 1].split(","))
            ki_placement.append(pairing)

        return tuple(ki_placement)

    @staticmethod
    def _vanilla_placement() -> tuple:
        return (
            Placement("bridge", "king"),
            Placement("lute", "sara"),
            Placement("ship", "bikke"),
            Placement("crown", "marsh"),
            Placement("crystal", "astos"),
            Placement("jolt_tonic", "matoya"),
            Placement("mystic_key", "elf"),
            Placement("nitro_powder", "locked_cornelia"),
            Placement("canal", "nerrick"),
            Placement("star_ruby", "vampire"),
            Placement("rod", "sarda"),
            Placement("canoe", "lukahn"),
            Placement("levistone", "ice"),
            Placement("airship", "desert"),
            Placement("rats_tail", "citadel_of_trials"),
            Placement("promotion", "bahamut"),
            Placement("bottle", "caravan"),
            Placement("oxyale", "fairy"),
            Placement("rosetta_stone", "mermaids"),
            Placement("lufienish", "dr_unne"),
            Placement("chime", "lefien"),
            Placement("warp_cube", "waterfall"),
            Placement("adamantite", "sky2"),
            Placement("excalibur", "smyth"),
            Placement("earth", "lich"),
            Placement("fire", "kary"),
            Placement("water", "kraken"),
            Placement("air", "tiamat"),
        )


STD_HEADER = """
#define WINDOW_TOP 0x0
#define WINDOW_BOTTOM 0x1
#define DIALOG_WAIT 0x1
#define DIALOG_AUTO_CLOSE 0x0
"""
