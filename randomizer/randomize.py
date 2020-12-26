#  Copyright 2020 Nicole Borrelli
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

import os
import random
from collections import namedtuple
from copy import deepcopy

from doslib.classes import JobClass
from doslib.dos_utils import load_tsv
from doslib.encounterregions import EncounterRegions
from doslib.enemy import EnemyStats, Encounter
from doslib.event import EventTables, EventTextBlock
from doslib.item import Item, Weapon
from doslib.items import Items
from doslib.map import Npc
from doslib.maps import Maps, MapFeatures, TreasureChest, ItemChest, MoneyChest
from doslib.rom import Rom
from doslib.shopdata import ShopData
from doslib.spells import Spells
from doslib.textblock import TextBlock
from event.easm import parse, link
from event.epp import pparse
from randomizer.clingo import solve_placement_for_seed
from randomizer.credits import add_credits
from randomizer.flags import Flags
from randomizer.hacks import trivial_enemies, enable_early_magic_buy
from randomizer.ipsfile import load_ips_files
from randomizer.placement import Placement, PlacementDetails
from randomizer.spellgenerator import SpellGenerator
from randomizer.treasure import InventoryGenerator
from stream.outputstream import OutputStream

VehiclePosition = namedtuple("VehiclePosition", ["x", "y"])


def load_vehicle_starts(rom: Rom) -> dict:
    vehicle_locations = rom.open_bytestream(0x65278, 16)
    return {
        "ship": VehiclePosition(x=vehicle_locations.get_u32(), y=vehicle_locations.get_u32()),
        "airship": VehiclePosition(x=vehicle_locations.get_u32(), y=vehicle_locations.get_u32())
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
        cls = JobClass(class_stats_stream)
        class_data.append(cls)
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


def load_enemy_data(rom: Rom, items: Items) -> list:
    enemy_data_stream = rom.open_bytestream(0x1DE044, 0x1860)
    enemies = []
    while not enemy_data_stream.is_eos():
        enemies.append(EnemyStats(enemy_data_stream))

    EnemyExtraData = namedtuple("EnemyExtraData",
                                ["enemy_index", "name", "max_hp", "atk", "pdef", "mdef", "drop_chance", "drop_type",
                                 "drop_item"])
    for item_data in load_tsv("data/EnemyData.tsv"):
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


def load_formation_data(rom: Rom, enemies: list):
    formation_data_stream = rom.open_bytestream(0x2288B4, 0x1CD4)

    formations = "\t".join(["formation_index", "power", "config", "unrunnable", "surprise_chance",
                            "enemy_1", "enemy_1_min", "enemy_1_max",
                            "enemy_2", "enemy_2_min", "enemy_2_max",
                            "enemy_3", "enemy_3_min", "enemy_3_max",
                            "enemy_4", "enemy_4_min", "enemy_4_max"]) + "\n"
    formation_configs = ["Small", "Large/Small", "Large", "Fiend", "Miniboss", "Flying", "DoS Boss"]
    formation_id = -1
    while not formation_data_stream.is_eos():
        formation = Encounter(formation_data_stream)
        monsters = ""
        power = 0
        formation_id += 1
        for monster in formation.groups:
            if monster.enemy_id == 0xff:
                monsters += f"None\t0\t0\t"
            else:
                monsters += f"{enemies[monster.enemy_id].name}\t{monster.min_count}\t{monster.max_count}\t"
                if enemies[monster.enemy_id].exp_reward == 1:
                    power += enemies[monster.enemy_id].gil_reward * monster.max_count
                else:
                    power += enemies[monster.enemy_id].exp_reward * monster.max_count

        if formation.unrunnable:
            unrunnable = "yes"
        else:
            unrunnable = "no"
        formations += f"{hex(formation_id)}\t{power}\t{formation_configs[formation.config]}\t{unrunnable}\t" \
                      f"{formation.surprise_chance}\t{monsters}\n"

    with open("formations.tsv", "w") as formation_tsv:
        formation_tsv.writelines(formations)


def load_chests(rom: Rom) -> list:
    chest_stream = rom.open_bytestream(0x217FB4, 0x400)
    chests = []
    while not chest_stream.is_eos():
        chest = TreasureChest.read(chest_stream)
        chests.append(chest)
    return chests


def pack_chests(chests: list) -> dict:
    chest_stream = OutputStream()
    for index, chest in enumerate(chests):
        chest.write(chest_stream)
    return {0x217FB4: chest_stream.get_buffer()}


def get_random_inventory_for_shop(map_index: int, shop_type: str, count: int, ids: bool,
                                  inventory_generator: InventoryGenerator) -> list:
    new_items = []

    # Cornelia Item Shop gets special treatment
    if map_index == 0x3E:
        items = inventory_generator.items.get_by_type("item")

        # Ensure Antidote and Gold Needle are in Cornelia
        new_items.append(items[0xb])
        new_items.append(items[0xc])

        # Make sure there aren't too many items there...
        count = max(count, 3)

    while len(new_items) < count:
        new_item = inventory_generator.get_inventory(map_index, shop_type)
        if new_item not in new_items:
            new_items.append(new_item)

    if ids:
        new_inventory = []
        for item in sorted(new_items, key=lambda it: it.sort_order):
            new_inventory.append(item.id)
        return new_inventory
    else:
        return new_items


def randomize_shops(rng: random.Random, maps: Maps, shops: ShopData, inventory_generator: InventoryGenerator):
    weapon_inventory = get_random_inventory_for_shop(0x0, "weapon", 40, False, inventory_generator)
    rng.shuffle(weapon_inventory)
    armor_inventory = get_random_inventory_for_shop(0x0, "armor", 40, False, inventory_generator)
    rng.shuffle(armor_inventory)

    for map_index in range(1, 0x76):
        map_features = maps.get_map(map_index)
        if len(map_features.shops) < 1:
            continue

        for shop_feature in map_features.shops:
            shop_inventories = shops.shop_inventories[shop_feature.event]

            if len(shop_inventories.items) > 0:
                count = rng.randint(3, 5)
                shop_inventories.items = get_random_inventory_for_shop(map_index, "item", count, True,
                                                                       inventory_generator)
            if len(shop_inventories.weapons) > 0:
                count = rng.randint(4, 6)
                items = []
                for index in range(0, count):
                    items.append(weapon_inventory.pop())
                items.sort(key=lambda it: it.sort_order)
                shop_inventories.weapons = list(map(lambda it: it.id, items))
            if len(shop_inventories.armor) > 0:
                count = rng.randint(4, 6)
                items = []
                for index in range(0, count):
                    items.append(armor_inventory.pop())
                items.sort(key=lambda it: it.sort_order)
                shop_inventories.armor = list(map(lambda it: it.id, items))
            elif len(shop_inventories.magic) > 0:
                # Magic shops don't get randomized as much as shuffled...
                continue


def randomize_treasure(rng: random.Random, maps: Maps, chests: list, inventory_generator: InventoryGenerator):
    for map_index in range(1, 0x76):
        map_features = maps.get_map(map_index)
        if len(map_features.chests) < 1:
            continue

        for map_chest in map_features.chests:
            chest = chests[map_chest.chest_id]
            if isinstance(chest, ItemChest) and chest.item_type == 0:
                # Key item or linked chest -- don't change it
                continue

            contents = inventory_generator.get_inventory(map_index)
            if contents.item_type == "gil":
                new_chest = MoneyChest(0x0)
                new_chest.qty = rng.randint(1, 0xfff) * rng.randint(1, 6)
            else:
                new_chest = ItemChest(0x80000000)
                new_chest.item_type = Items.name_to_index(contents.item_type)
                new_chest.item_id = contents.id
            chests[map_chest.chest_id] = new_chest


def spell_shuffle(maps: Maps, shops: ShopData, spells: Spells, spell_generator: SpellGenerator):
    original_spells = deepcopy(spells)
    for map_index in range(1, 0x76):
        map_features = maps.get_map(map_index)
        if len(map_features.shops) < 1:
            continue

        # Don't touch the caravan.
        if map_index in [0x72, 0x73]:
            continue

        for shop_feature in map_features.shops:
            shop_inventories = shops.shop_inventories[shop_feature.event]
            if len(shop_inventories.magic) == 0:
                continue

            new_inventory = []
            first_spell = shop_inventories.magic[0]
            school = "white" if first_spell <= 32 else "black"
            spell_level = int(first_spell / 4) + 1 if school == "white" else int((first_spell - 32) / 4) + 1
            for slot_index in range(0, len(shop_inventories.magic)):
                spell_index = shop_inventories.magic[slot_index]
                spell = spell_generator.get_inventory(map_index, school)
                orig_spell = original_spells.spell_data[spell_index]

                # Put the spell for sale in this shop
                new_inventory.append(spell.spell_index)

                # Update the level of the spell for real
                spells.spell_data[spell.spell_index].level = spell_level
                spells.spell_data[spell.spell_index].price = orig_spell.price
                if spell_level <= 2:
                    spells.spell_data[spell.spell_index].mp_cost = orig_spell.mp_cost

                spells.permissions[spell.spell_index] = spells.shuffled_permission[spell_index]
            shop_inventories.magic = new_inventory


def prevent_canal_soft_lock(overworld: MapFeatures):
    # The easiest way to do this is create an NPC and place them on top of the canal spot.
    # This prevents walking across and the airship landing there.
    canal_splash = Npc()
    canal_splash.identifier = 0x2
    canal_splash.in_room = 0x1
    canal_splash.x_pos = 95
    canal_splash.y_pos = 157
    canal_splash.move_speed = 0
    canal_splash.event = 0x1f62
    canal_splash.sprite_id = 0xC6
    overworld.npcs.append(canal_splash)


def map_updates(maps: Maps):
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
        door_map = maps.get_map(map_id)
        for sprite in door_map.sprites:
            if sprite.event == 0x23cd:
                sprite.event = 0x1f4a

    # In the vanilla game, you grab the Star Ruby from behind the Vampire, leave Earth Cave,
    # visit Sarda, get the Rod, and come back to open the plate. In theory, in HMS Janye you
    # could find the Rod behind the Vampire. In this case the event on the Earth Plate would
    # be the basic "You sense something evil" event rather than the event that will break it
    # open if you have the Rod.
    #
    # To fix this, we always have the Rod script on the tablet, and just have a check in that
    # script for the Rod, printing the "evil" text if the player doesn't have it.
    maps.get_map(0x3).npcs[0xe].event = 0x139c

    # There could be fewer bats... This also makes room for features in other maps.
    bat_mania_maps = [
        0x2,  # Earth B2
        0x4,  # Earth B4
    ]

    for map_id in bat_mania_maps:
        bat_map = maps.get_map(map_id)
        fewer_bats = []
        for index, npc in enumerate(bat_map.npcs):
            if npc.event == 0x200c:
                if index % 2 == 0:
                    fewer_bats.append(npc)
            else:
                fewer_bats.append(npc)
        bat_map.npcs = fewer_bats

    prevent_canal_soft_lock(maps.get_map(0x0))

    # Citadel of trials -- can enter w/o the stolen Crown
    citadel_of_trials = maps.get_map(0x4d)
    citadel_of_trials.npcs = []
    for tile in citadel_of_trials.tiles:
        if tile.event == 0x23d0:
            citadel_of_trials.tiles.remove(tile)


def load_event_scripts() -> dict:
    scripts = {}
    for file in os.listdir("scripts/"):
        if file.endswith(".script"):
            add_events = parse_script(f"scripts/{file}")
            for event_id, source in add_events.items():
                scripts[event_id] = source
    return scripts


def parse_script(script: str) -> dict:
    events = {}
    script_id = None
    script_code = ""
    with open(script, "r") as script_text:
        for line in script_text.readlines():
            if line.startswith("begin script="):
                if script_id is not None:
                    events[script_id] = script_code
                    script_code = ""
                script_id = int(line[line.find("=") + 1:], 0)
            elif script_id is not None:
                script_code += line
    if script_id is not None:
        events[script_id] = script_code
    return events


def build_headers(placements: Placement) -> str:
    header = """
    ; Standard defines
    #define WINDOW_TOP 0x0
    #define WINDOW_BOTTOM 0x1
    #define DIALOG_WAIT 0x1
    #define DIALOG_AUTO_CLOSE 0x0
    
    #define FREE_START set_flag 0x05
    
    ; Reward definitions
    """

    text_ids = ""
    flag_names = ""
    for placement in placements.all_placements():
        flag = f"\tset_flag {hex(placement.plot_flag)}\\\n" if placement.plot_flag is not None else ""
        item = f"\tgive_item {hex(placement.plot_item)}\\\n" if placement.plot_item is not None else ""
        extra = f"\t{placement.extra}\n" if placement.extra is not None else ""
        header += f"#define GIVE_{placement.source.upper()}_REWARD \\\n{flag}{item}{extra}\n"
        text_ids += f"%{placement.source.lower()}_text_id {hex(placement.reward_text_id)}\n"
        flag_names += f"%{placement.source.lower()}_reward_flag {hex(placement.plot_flag)}\n"

        # One special case for "flags" -- note the sprite for the desert location
        if placement.source == "desert":
            flag_names += f"%desert_reward_sprite {hex(placement.sprite)}\n"

    header += f"\n;String ID references\n{text_ids}\n\n;Plot flags\n{flag_names}\n\n"
    return header


def update_strings(event_text: EventTextBlock):
    with open("data/TextUpdates.tsv", "r") as text_data:
        for line in text_data.readlines():
            string_num, text = line.strip().split('\t')
            string_num = int(string_num, 16)

            if not text.endswith('\x00'):
                text += '\x00'

            event_text.strings[string_num] = TextBlock.encode_text(text)


def pick_gear_reward(rng: random.Random, gear_placement: PlacementDetails,
                     inventory_generator: InventoryGenerator) -> Item:
    gear_type = rng.choice(["weapon", "armor"])
    grades = ["S", "A"] if gear_placement.zone in ["inner", "early"] else ["S"]
    options = []
    for grade in grades:
        if grade in inventory_generator.item_grades:
            for item in inventory_generator.item_grades[grade]:
                if item.item_type == gear_type:
                    options.append(item)

    choice = rng.choice(options)
    if gear_placement.zone == "early":
        # If the gear falls onto the King, Sara, or Bikke, make sure at least one unpromoted class can use it
        while choice.equip_classes & 0x3f == 0:
            choice = rng.choice(options)
    return choice


def randomize(rom_data: bytearray, seed: str, flags: Flags) -> bytearray:
    print(f"Randomizing with seed {seed}, {flags.encode()}")

    # Start with the list of standard patches to improve gameplay.
    all_patches = load_ips_files("patches/DataPointerConsolidation.ips",
                                 "patches/Earth__CitadelMap.ips",
                                 "patches/EventUpdates.ips",
                                 "patches/FF1EncounterToggle.ips",
                                 "patches/ImprovedEquipmentStatViewing.ips",
                                 "patches/NoEscape.ips",
                                 "patches/RunningChange.ips",
                                 "patches/SpellLevelFix.ips",
                                 "patches/SpriteFrameLoaderFix.ips",
                                 "patches/StatusScreenExpansion.ips")
    all_patches.update(enable_early_magic_buy())

    rom = Rom(rom_data)

    rng = random.Random()
    rng.seed(seed)

    event_text_block = EventTextBlock(rom)
    shop_data = ShopData(rom)
    spells = Spells(rom)
    chest_data = load_chests(rom)
    map_features = Maps(rom)
    vehicle_starts = load_vehicle_starts(rom)

    items = Items(rom)
    enemy_data = load_enemy_data(rom, items)

    # Don't load formation data (since we don't do anything with it)
    # load_formation_data(rom, enemy_data)

    encounter_regions = EncounterRegions(rom)
    for region in encounter_regions.overworld_regions:
        rng.shuffle(region)
    for region in encounter_regions.map_encounters:
        rng.shuffle(region)

    classes_data = load_class_data(rom)
    if not flags.default_start_gear:
        base_weapons = []
        base_armors = []

        # Find weapons & armor that can be used by the base classes
        for weapon in items.get_by_type("weapon"):
            if weapon.id > 0 and weapon.equip_classes & 0x003f != 0:
                base_weapons.append(weapon)
        for armor in items.get_by_type("armor"):
            if 0x1b >= armor.id > 0 != armor.equip_classes & 0x003f:
                base_armors.append(armor)

        class_bit = 0x1
        for class_data in classes_data:
            class_weapons = []
            class_armors = []
            for weapon in base_weapons:
                if weapon.equip_classes & class_bit != 0:
                    class_weapons.append(weapon)
            for armor in base_armors:
                if armor.equip_classes & class_bit != 0:
                    class_armors.append(armor)
            class_data.weapon_id = rng.choice(class_weapons).id
            class_data.armor_id = rng.choice(class_armors).id
            class_bit = class_bit << 1

        all_patches.update(pack_class_data(classes_data))

    if flags.scale_levels != 1.0:
        level_reqs = load_xp_requirements(rom)
        scaled_level_reqs = []
        for level_req in level_reqs:
            scaled_level_reqs.append(int(level_req * flags.scale_levels))
        all_patches.update(pack_xp_requirements(scaled_level_reqs))

    inventory_generator = InventoryGenerator(seed, items)
    if not flags.standard_shops:
        randomize_shops(rng, map_features, shop_data, inventory_generator)

        spell_generator = SpellGenerator(seed, spells)
        spell_shuffle(map_features, shop_data, spells, spell_generator)

    inventory_generator.update_with_new_shops(shop_data)
    if not flags.standard_treasure:
        randomize_treasure(rng, map_features, chest_data, inventory_generator)

    # The key feature of HMS Janye is starting with the Ship (the HMS Janye), so move the ship to Cornelia harbor.
    vehicle_starts["ship"] = VehiclePosition(x=2328, y=2600)

    # Do some basic updates to the maps
    map_updates(map_features)

    # Are Key Items being shuffled? If so, figure out their placement.
    placement = Placement()
    if not flags.no_shuffle:
        rng = random.Random()
        rng.seed(seed)
        placement.update_placements(solve_placement_for_seed(rng.randint(0, 0xffffffff)))

    # Generate a nice piece of gear for the 'gear' position
    gear_placement = placement.find_gear()
    gear = pick_gear_reward(rng, gear_placement, inventory_generator)
    placement.update_gear(gear)
    event_text_block.strings[0x47c] = TextBlock.encode_text(f"You obtain: {gear.name}\x00")

    # This doesn't have to be done unless shuffling key items, but doing it this way allows a player
    # to see how certain items are represented better, so we do it anyway.
    for ki_placement in placement.all_placements():
        # If this is the airship, reset where it comes out.
        if ki_placement.reward == "airship":
            vehicle_starts["airship"] = VehiclePosition(x=ki_placement.airship_x, y=ki_placement.airship_y)

        # This is really just for the desert, but this feels safer, somehow?
        if ki_placement.map_id is None:
            continue

        if ki_placement.type == 'npc':
            npc_map = map_features.get_map(ki_placement.map_id)
            npc_map.npcs[ki_placement.index].sprite_id = ki_placement.sprite

            # Some sprites weren't designed to move, so hold them still.
            if not ki_placement.movable:
                npc_map.npcs[ki_placement.index].move_speed = 0

            # Princess Sara is both in Cornelia Castle, where she gives the player the lute, and in the
            # Temple of Fiends, having been kidnapped by Garland at the start of the game.
            if ki_placement.source == "sara":
                tof_map = map_features.get_map(0x1f)
                princess_sara_index = tof_map.find_npc(0x0)
                tof_map.npcs[princess_sara_index].sprite_id = ki_placement.sprite
                tof_map.npcs[princess_sara_index].move_speed = 0

        elif ki_placement.type == 'chest':
            chest_map = map_features.get_map(ki_placement.map_id)
            chest, sprite = chest_map.get_event_chest(ki_placement.index)
            chest_map.chests.remove(chest)
            chest_map.sprites.remove(sprite)

            chest_npc = Npc()
            chest_npc.identifier = 0x2
            chest_npc.in_room = 0x1
            chest_npc.x_pos = sprite.x_pos
            chest_npc.y_pos = sprite.y_pos
            chest_npc.move_speed = 0
            chest_npc.event = sprite.event

            if ki_placement.map_id in [0x38, 0x5b, 0x1e]:
                # Use a chest in Cornelia, Marsh, and the mermaid floor in Sea.
                chest_npc.sprite_id = 0xc7
            else:
                chest_npc.sprite_id = ki_placement.sprite
            chest_map.npcs.append(chest_npc)
        else:
            raise RuntimeError(f"Unknown placement type: {ki_placement.type} at {ki_placement.source}")

    headers = build_headers(placement)
    event_scripts = load_event_scripts()

    # Update game strings.
    update_strings(event_text_block)
    all_patches.update(event_text_block.pack())

    event_tables = EventTables(rom)
    event_script_patches = {}
    for event_id in sorted(event_scripts.keys()):
        script = event_scripts[event_id]
        preprocess = pparse(f"{headers}\n\n{script}")
        event_icode = parse(preprocess)

        event_addr = event_tables.get_addr(event_id)
        vanilla_size = rom.get_event_size(event_addr)

        # If the event doesn't fit in the vanilla location, move it to part of our free space.
        if event_icode.size > vanilla_size:
            event_addr = rom.get_free_space(f"event_{hex(event_id)}", event_icode.size)

        event_script_patches[Rom.pointer_to_offset(event_addr)] = link(event_icode, event_addr)
        event_tables.set_addr(event_id, event_addr)

    if flags.debug:
        trivial_enemies(enemy_data)

    all_patches.update(add_credits(rom, seed, flags))

    all_patches.update(event_script_patches)
    all_patches.update(event_tables.get_patches())
    all_patches.update(map_features.get_patches())
    all_patches.update(items.get_patches())
    all_patches.update(shop_data.get_patches())
    all_patches.update(spells.get_patches())
    all_patches.update(encounter_regions.get_patches())
    all_patches.update(pack_enemy_data(enemy_data))
    all_patches.update(pack_chests(chest_data))
    all_patches.update(pack_vehicle_starts(vehicle_starts))

    randomized_rom = rom.apply_patches(all_patches)

    return randomized_rom.rom_data
