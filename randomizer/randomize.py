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

import random

from doslib.rom import Rom
from doslib.textblock import TextBlock
from randomizer.clingo import solve_placement_for_seed
from randomizer.credits import add_credits
from randomizer.events import compile_event_scripts, load_event_scripts, update_strings
from randomizer.options import RandomizerOptions
from randomizer.game_data import (
    VehiclePosition,
    load_game_data,
    load_xp_requirements,
    pack_chests,
    pack_class_data,
    pack_encounter_data,
    pack_enemy_data,
    pack_vehicle_starts,
    pack_xp_requirements,
)
from randomizer.gear import pick_gear_reward, randomize_starting_gear
from randomizer.hacks import trivial_enemies, enable_early_magic_buy
from randomizer.ipsfile import load_ips_files
from randomizer.map_updates import map_updates
from randomizer.patchset import PatchSet
from randomizer.placement import Placement
from randomizer.placement_application import apply_placements
from randomizer.progress import NullProgressReporter, ProgressReporter
from randomizer.seed import normalize_seed
from randomizer.shops import randomize_shops
from randomizer.spellgenerator import SpellGenerator
from randomizer.spells import spell_shuffle
from randomizer.trace import RandomizerTrace
from randomizer.treasure import InventoryGenerator, randomize_treasure


def randomize(rom_data: bytearray, seed: str, options: RandomizerOptions,
              data_source=None,
              trace: RandomizerTrace | None = None,
              progress: ProgressReporter | None = None) -> bytearray:
    seed = normalize_seed(seed)
    progress = progress if progress is not None else NullProgressReporter()
    progress.update("start", f"Randomizing with seed {seed}, {options.short_code()}")

    # Start with the list of standard patches to improve gameplay.
    all_patches = PatchSet()
    all_patches.update(load_ips_files("patches/DataPointerConsolidation.ips",
                                      "patches/Earth__CitadelMap.ips",
                                      "patches/EventUpdates.ips",
                                      "patches/FF1EncounterToggle.ips",
                                      "patches/ImprovedEquipmentStatViewing.ips",
                                      "patches/NoEscape.ips",
                                      "patches/RunningChange.ips",
                                      "patches/SpellLevelFix.ips",
                                      "patches/SpriteFrameLoaderFix.ips",
                                      "patches/StatusScreenExpansion.ips",
                                      data_source=data_source), source="base patches")
    all_patches.update(enable_early_magic_buy(), source="early magic")

    rom = Rom(rom_data)

    rng = random.Random()
    rng.seed(seed)

    data = load_game_data(rom, options, data_source, trace)
    event_text_block = data.event_text
    shop_data = data.shop_data
    spells = data.spells
    chest_data = data.chests
    map_features = data.maps
    boss_data = data.bosses
    vehicle_starts = data.vehicle_starts
    encounters = data.encounters
    items = data.items
    enemy_data = data.enemies
    encounter_regions = data.encounter_regions
    classes_data = data.classes

    for region in encounter_regions.overworld_regions:
        rng.shuffle(region)
    for region in encounter_regions.map_encounters:
        rng.shuffle(region)

    if options.randomize_bosses:
        boss_data.randomize_bosses(encounters, enemy_data, rng)

    inventory_generator = InventoryGenerator(seed, items, options.new_item_distribution, data_source)
    if options.randomize_shops:
        randomize_shops(rng, map_features, shop_data, inventory_generator)

        spell_generator = SpellGenerator(seed, spells, data_source)
        spell_shuffle(map_features, shop_data, spells, spell_generator)

    inventory_generator.update_with_new_shops(shop_data)
    if options.randomize_treasure:
        randomize_treasure(rng, map_features, chest_data, inventory_generator)

    if options.randomize_starting_gear:
        classes_data = randomize_starting_gear(rng, items, classes_data)
        all_patches.update(pack_class_data(classes_data), source="class data")

    if options.xp_rate_percent != 100:
        level_reqs = load_xp_requirements(rom)
        scaled_level_reqs = []
        for level_req in level_reqs:
            scaled_level_reqs.append((level_req * 100) // options.xp_rate_percent)
        all_patches.update(pack_xp_requirements(scaled_level_reqs), source="xp requirements")

    # Do some basic updates to the maps
    map_updates(map_features)

    # String to insert for free items at the start (usually the ship + bridge)
    free_header = ""

    # Update game strings -- do this _before_ updating placements or the strings for gear won't replace them.
    update_strings(event_text_block, data_source)

    # Are Key Items being shuffled? If so, figure out their placement.
    placement = Placement(data_source)
    if options.shuffle_key_items:
        free_items = ["bridge", "ship"]

        rng = random.Random()
        rng.seed(seed)
        clingo_placements = solve_placement_for_seed(rng.randint(0, 0xffffffff))
        placement.update_placements(clingo_placements)

        # The key feature of HMS Janye is starting with the Ship (the HMS Janye), so move the ship to Cornelia harbor.
        vehicle_starts["ship"] = VehiclePosition(x=2328, y=2600)

        # At the moment it doesn't really matter, but we only want to give the free items once when the game
        # starts, which would allow us to give a starter pack at some point. To do this check, we need to
        # check for a particular plot flag.
        # This check _could_ be made to work even without any free key items, but since this is HMS Jayne anyway,
        # I'll keep the logic simple by assuming we have access to at least one.

        # If a given placement is "free", put a piece of gear in its place
        free_cmds = []
        for ki_placement in placement.all_placements():
            if ki_placement.reward in free_items:
                # Before replacing the item, grab the commands needed to give the item
                if ki_placement.plot_flag is not None:
                    free_cmds.append(f"set_flag {hex(ki_placement.plot_flag)}")
                if ki_placement.plot_item is not None:
                    free_cmds.append(f"give_item {hex(ki_placement.plot_item)}")
                if ki_placement.extra is not None:
                    free_cmds.append(f"{ki_placement.extra}")

                gear = pick_gear_reward(rng, ki_placement, inventory_generator)
                placement.update_gear(ki_placement.reward, gear)
                event_text_block.strings[ki_placement.reward_text_id] = TextBlock.encode_text(
                    f"You obtain: {gear.name}\x00")

        free_header = "#define FREE_START " + "\\\n".join(free_cmds)
    else:
        # We have to define FREE_START even though progress is vanilla. The safe thing to do
        # is just set flag 0x28, which is the flag that usually means we've talked to the
        # guards in Cornelia/listened to the King.
        # In HMS Jayne this _usually_ gets mapped to the first piece of free gear the party gets, but
        # since there aren't any gear replacements, it's safe to use here.
        free_header = "#define FREE_START set_flag 0x28"

    apply_placements(placement, map_features, vehicle_starts)

    if trace is not None:
        trace.checkpoint(
            "placements",
            shuffled=options.shuffle_key_items,
            placements=[placement._asdict() for placement in placement.all_placements()],
        )
        trace.checkpoint(
            "vehicle_starts",
            ship={"x": vehicle_starts["ship"].x, "y": vehicle_starts["ship"].y},
            airship={"x": vehicle_starts["airship"].x, "y": vehicle_starts["airship"].y},
        )

    event_scripts = load_event_scripts(data_source)

    all_patches.update(event_text_block.pack(), source="event text")

    event_script_patches, event_table_patches = compile_event_scripts(
        rom, placement, free_header, event_scripts
    )

    if options.debug:
        trivial_enemies(enemy_data)

    all_patches.update(add_credits(rom, seed, options), source="credits")
    all_patches.update(event_script_patches, source="event scripts")
    all_patches.update(event_table_patches, source="event tables")
    all_patches.update(map_features.get_patches(), source="maps")
    all_patches.update(items.get_patches(), source="items")
    all_patches.update(shop_data.get_patches(), source="shops")
    all_patches.update(spells.get_patches(), source="spells")
    all_patches.update(encounter_regions.get_patches(), source="encounter regions")
    all_patches.update(boss_data.get_patches(), source="bosses")
    all_patches.update(pack_encounter_data(encounters), source="encounters")
    all_patches.update(pack_enemy_data(enemy_data), source="enemies")
    all_patches.update(pack_chests(chest_data), source="chests")
    all_patches.update(pack_vehicle_starts(vehicle_starts), source="vehicles")

    if trace is not None:
        trace.record_patches(all_patches)

    randomized_rom = rom.apply_patches(all_patches)
    progress.update("complete", "Randomization Finished")
    return randomized_rom.rom_data
