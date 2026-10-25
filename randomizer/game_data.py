#  Copyright 2026 HMS Jayne contributors
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

"""ROM and TSV loading for one randomizer run."""

from collections import namedtuple
from dataclasses import dataclass

from doslib.classes import JobClass
from doslib.dos_utils import load_tsv
from doslib.encounterregions import EncounterRegions
from doslib.enemy import EnemyStats, Encounter
from doslib.event import EventTextBlock
from doslib.items import Items
from doslib.maps import Maps, TreasureChest
from doslib.rom import Rom
from doslib.shopdata import ShopData
from doslib.spells import Spells
from randomizer.bossshuffle import BossData
from randomizer.flags import Flags
from randomizer.trace import RandomizerTrace
from stream.outputstream import OutputStream

VehiclePosition = namedtuple("VehiclePosition", ["x", "y"])

EnemyExtraData = namedtuple(
    "EnemyExtraData",
    ["enemy_index", "name", "max_hp", "atk", "pdef", "mdef", "drop_chance", "drop_type", "drop_item"],
)


@dataclass
class GameData:
    event_text: EventTextBlock
    shop_data: ShopData
    spells: Spells
    chests: list
    maps: Maps
    bosses: BossData
    vehicle_starts: dict
    encounters: list
    items: Items
    enemies: list
    encounter_regions: EncounterRegions
    classes: list


def load_vehicle_starts(rom: Rom) -> dict:
    vehicle_locations = rom.open_bytestream(0x65278, 16)
    return {
        "ship": VehiclePosition(x=vehicle_locations.get_u32(), y=vehicle_locations.get_u32()),
        "airship": VehiclePosition(x=vehicle_locations.get_u32(), y=vehicle_locations.get_u32()),
    }


def pack_vehicle_starts(starts: dict) -> dict:
    vehicle_starts = OutputStream()
    vehicle_starts.put_u32(starts["ship"].x)
    vehicle_starts.put_u32(starts["ship"].y)
    vehicle_starts.put_u32(starts["airship"].x)
    vehicle_starts.put_u32(starts["airship"].y)
    return {0x65278: vehicle_starts.get_buffer()}


def load_class_data(rom: Rom) -> list:
    class_stats_stream = rom.open_bytestream(0x1E1354, 96)
    class_data = []
    while not class_stats_stream.is_eos():
        class_data.append(JobClass(class_stats_stream))
    return class_data


def pack_class_data(classes_data: list) -> dict:
    class_stats_stream = OutputStream()
    for class_data in classes_data:
        class_data.write(class_stats_stream)
    return {0x1e1354: class_stats_stream.get_buffer()}


def load_xp_requirements(rom: Rom) -> list:
    level_data = rom.open_bytestream(0x1BE3B4, 396)
    exp_for_level = []
    while not level_data.is_eos():
        exp_for_level.append(level_data.get_u32())
    return exp_for_level


def pack_xp_requirements(exp_for_level: list) -> dict:
    level_data = OutputStream()
    for exp in exp_for_level:
        level_data.put_u32(exp)
    return {0x1BE3B4: level_data.get_buffer()}


def load_enemy_data(rom: Rom, items: Items, fiend_ribbons: bool, data_source=None) -> list:
    enemy_data_stream = rom.open_bytestream(0x1DE044, 0x1860)
    enemies = []
    while not enemy_data_stream.is_eos():
        enemies.append(EnemyStats(enemy_data_stream))

    file_name = "data/EnemyData_2.tsv" if fiend_ribbons else "data/EnemyData.tsv"
    for item_data in load_tsv(file_name, data_source):
        extra = EnemyExtraData(*item_data)
        enemies[extra.enemy_index].name = extra.name
        enemies[extra.enemy_index].max_hp = extra.max_hp
        enemies[extra.enemy_index].atk = extra.atk
        enemies[extra.enemy_index].pdef = extra.pdef
        enemies[extra.enemy_index].mdef = extra.mdef
        enemies[extra.enemy_index].drop_chance = extra.drop_chance
        if extra.drop_type is not None:
            drop_item = items.find_by_type(extra.drop_type, extra.drop_item)
            enemies[extra.enemy_index].drop_type = Items.name_to_index(extra.drop_type)
            enemies[extra.enemy_index].drop_id = drop_item.id

    return enemies


def pack_enemy_data(enemies: list) -> dict:
    out = OutputStream()
    for enemy in enemies:
        enemy.write(out)
    return {
        0x1DE044: out.get_buffer()
    }


def load_encounter_data(rom: Rom) -> list:
    encounter_stream = rom.open_bytestream(0x2288B4, 0x1CD4)
    formations = []
    while not encounter_stream.is_eos():
        formations.append(Encounter(encounter_stream))
    return formations


def pack_encounter_data(encounters: list) -> dict:
    out = OutputStream()
    for encounter in encounters:
        encounter.write(out)
    return {
        0x2288B4: out.get_buffer(),
        0x22D3E4: out.get_buffer()
    }


def load_chests(rom: Rom) -> list:
    chest_stream = rom.open_bytestream(0x217FB4, 0x400)
    chests = []
    while not chest_stream.is_eos():
        chests.append(TreasureChest.read(chest_stream))
    return chests


def pack_chests(chests: list) -> dict:
    chest_stream = OutputStream()
    for chest in chests:
        chest.write(chest_stream)
    return {0x217FB4: chest_stream.get_buffer()}


def load_game_data(rom: Rom, flags: Flags, data_source=None,
                   trace: RandomizerTrace | None = None) -> GameData:
    event_text = EventTextBlock(rom)
    shop_data = ShopData(rom)
    spells = Spells(rom, data_source)
    chests = load_chests(rom)
    maps = Maps(rom)
    bosses = BossData(rom, data_source)
    vehicle_starts = load_vehicle_starts(rom)
    encounters = load_encounter_data(rom)
    items = Items(rom, flags.new_items, data_source)
    enemies = load_enemy_data(rom, items, flags.fiend_ribbons, data_source)
    encounter_regions = EncounterRegions(rom)
    classes = load_class_data(rom)

    if trace is not None:
        trace.checkpoint(
            "data_loaded",
            enemies=len(enemies),
            chests=len(chests),
            shops=len(shop_data.shop_inventories),
            spells=len(spells.spell_data),
            encounters=len(encounters),
        )

    return GameData(
        event_text=event_text,
        shop_data=shop_data,
        spells=spells,
        chests=chests,
        maps=maps,
        bosses=bosses,
        vehicle_starts=vehicle_starts,
        encounters=encounters,
        items=items,
        enemies=enemies,
        encounter_regions=encounter_regions,
        classes=classes,
    )
