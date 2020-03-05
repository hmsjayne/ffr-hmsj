#!/usr/bin/env python3

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
import os
import random
from argparse import ArgumentParser
from random import randint

from ips_util import Patch

from doslib.event import EventTextBlock
from doslib.gen.classes import JobClass
from doslib.gen.enemy import EnemyStats
from doslib.gen.items import Weapon, Armor
from doslib.rom import Rom
from doslib.textblock import TextBlock
from randomizer.credits import add_credits
from randomizer.flags import Flags
from randomizer.formations import FormationRandomization
from randomizer.keyitemsolver import KeyItemPlacement
from randomizer.randomtreasure import random_bucketed_treasures
from randomizer.spellshuffle import SpellShuffle
from randomizer.treasures import treasure_shuffle
from stream.outputstream import OutputStream

BASE_PATCHES = [
    "data/DataPointerConsolidation.ips",
    "data/ImprovedEquipmentStatViewing.ips",
    "data/NoEscape.ips",
    "data/RunningChange.ips",
    "data/StatusScreenExpansion.ips",
    "data/SpellLevelFix.ips",
    "data/SpriteFrameLoaderFix.ips",
    "data/EventUpdates.ips",
    "data/Earth__CitadelMap.ips",
]


def randomize_rom(rom: Rom, flags: Flags, rom_seed: str) -> Rom:
    rng = random.Random()
    rng.seed(rom_seed)

    print(f"Randomize ROM: {flags.text()}, seed='{rom_seed}'")
    patches_to_load = BASE_PATCHES
    if flags.encounters is not None:
        patches_to_load.append("data/FF1EncounterToggle.ips")
    if flags.default_party is not None:
        patches_to_load.append("data/RandomDefault.ips")

    patched_rom_data = rom.rom_data

    for patch_path in patches_to_load:
        patch = Patch.load(patch_path)
        patched_rom_data = patch.apply(patched_rom_data)
    rom = Rom(data=bytearray(patched_rom_data))

    rom = add_credits(rom)

    event_text_block = EventTextBlock(rom)
    event_text_block.shrink()
    rom = event_text_block.pack(rom)

    rom = update_xp_requirements(rom, flags.exp_mult)

    if flags.key_item_shuffle is not None:
        placement = KeyItemPlacement(rom, rng.randint(0, 0xffffffff))
    else:
        placement = KeyItemPlacement(rom)
    rom = placement.rom

    if flags.magic is not None:
        shuffle_magic = SpellShuffle(rom, rng)
        rom = shuffle_magic.write(rom)

    if flags.treasures is not None:
        if flags.treasures == "shuffle":
            rom = treasure_shuffle(rom, rng)
        else:
            rom = random_bucketed_treasures(rom, rng, flags.wealth)

    if flags.debug is not None:
        class_stats_stream = rom.open_bytestream(0x1E1354, 96)
        class_stats = []
        while not class_stats_stream.is_eos():
            class_stats.append(JobClass(class_stats_stream))

        class_out_stream = OutputStream()
        for job_class in class_stats:
            # Set the starting weapon and armor for all classes to something
            # very fair and balanced: Masamune + Diamond Armlet. :)
            job_class.weapon_id = 0x28
            job_class.armor_id = 0x0e

            # Write the (very balanced) new data out
            job_class.write(class_out_stream)

        rom = rom.apply_patch(0x1E1354, class_out_stream.get_buffer())
    elif flags.start_gear is not None:
        class_stats_stream = rom.open_bytestream(0x1E1354, 96)
        class_stats = []
        while not class_stats_stream.is_eos():
            class_stats.append(JobClass(class_stats_stream))

        weapon_stream = rom.open_bytestream(0x19F33C, 0x71C)
        weapons = []
        while not weapon_stream.is_eos():
            weapons.append(Weapon(weapon_stream))

        armor_stream = rom.open_bytestream(0x19FA58, 0x7C4)
        armors = []
        while not armor_stream.is_eos():
            armors.append(Armor(armor_stream))

        class_bit = 0x1
        class_out_stream = OutputStream()
        for job_class in class_stats:
            pick_weapon = 0
            while pick_weapon == 0 or weapons[pick_weapon].equip_classes & class_bit == 0:
                pick_weapon = rng.randint(0, len(weapons))

            pick_armor = 0
            while pick_armor == 0 or armors[pick_armor].equip_classes & class_bit == 0:
                pick_armor = rng.randint(0, 0x1B)

            job_class.weapon_id = pick_weapon
            job_class.armor_id = pick_armor
            class_bit = class_bit << 1

            # Write the (very balanced) new data out
            job_class.write(class_out_stream)

        rom = rom.apply_patch(0x1E1354, class_out_stream.get_buffer())

    if flags.shuffle_formations:
        formation = FormationRandomization(rom, rng)
        rom = rom.apply_patches(formation.patches())

    if True:
        enemy_data_stream = rom.open_bytestream(0x1DE044, 0x1860)
        enemies = []
        while not enemy_data_stream.is_eos():
            enemies.append(EnemyStats(enemy_data_stream))

        # Rebalance (Revisited) Fiend HP
        enemies[0x78].max_hp = enemies[0x77].max_hp * 2
        enemies[0x7a].max_hp = enemies[0x79].max_hp * 2
        enemies[0x7c].max_hp = enemies[0x7b].max_hp * 2
        enemies[0x7e].max_hp = enemies[0x7d].max_hp * 2

        # And Chaos
        enemies[0x7f].max_hp = enemies[0x7e].max_hp * 2

        # Finally, Piscodemons can suck it
        enemies[0x67].atk = int(enemies[0x67].atk / 2)

        # We'll also lower everyone's INT just to see how that works
        for index in range(0x80):
            enemies[index].intel = int(.666 * enemies[index].intel)
            # print(f"{hex(index)} HP: {enemies[index].max_hp}, INT: {enemies[index].intel}")

        out = OutputStream()
        for enemy in enemies:
            enemy.write(out)
        rom = rom.apply_patch(0x1DE044, out.get_buffer())

    # Add the seed + flags to the party creation screen.
    seed_str = TextBlock.encode_text(f"Seed:\n{rom_seed}\nFlags:\n{flags}\x00")
    pointer = OutputStream()
    pointer.put_u32(0x8227054)
    rom = rom.apply_patches({
        0x227054: seed_str,
        0x4d8d4: pointer.get_buffer()
    })

    return rom


def gen_seed(rom_seed: str) -> str:
    """Reduces a seed to the first 10 chars.

    Pulling this out for future caching, should we desire.
    :param rom_seed: Raw input seed
    :return: String of the seed
    """
    if rom_seed is None:
        rom_seed = hex(randint(0, 0xffffffff))
    elif len(rom_seed) > 10:
        rom_seed = rom_seed[0:10]

    out_seed = rom_seed
    return str(out_seed)


def get_filename(base_path: str, flags: Flags, rom_seed: str) -> str:
    filename = base_path
    if filename.find(os.sep) > -1:
        filename = filename[0:filename.rfind(os.sep)]
    if filename.lower().endswith(".gba"):
        filename = filename[:len(filename) - 4]
    return f"{filename}_{flags.text()}_{rom_seed}.gba"


def randomize(rom_path: str, flags: Flags, rom_seed: str):
    rom_seed = gen_seed(rom_seed)
    vanilla_rom = Rom(rom_path)
    rom = randomize_rom(vanilla_rom, flags, rom_seed)

    rom.write(get_filename(rom_path, flags, rom_seed))


def update_xp_requirements(rom: Rom, value) -> Rom:
    level_data = rom.open_bytestream(0x1BE3B4, 396)
    new_table = OutputStream()
    next_value = level_data.get_u32()
    while next_value is not None:
        new_table.put_u32(int(next_value * value))
        next_value = level_data.get_u32()
    rom = rom.apply_patch(0x1BE3B4, new_table.get_buffer())
    return rom


def main() -> int:
    parser = ArgumentParser(description="Final Fantasy Dawn of Souls Randomizer")
    parser.add_argument("rom", metavar="ROM file", type=str, help="The ROM file to randomize.")
    parser.add_argument("--seed", dest="seed", nargs=1, type=str, action="append", help="Seed value to use")
    parser.add_argument("--flags", dest="flags", nargs=1, type=str, action="append", required=True, help="Flags")
    parsed = parser.parse_args()

    # Ensure there's at most 1 seed.
    if parsed.seed is not None:
        seed_list = parsed.seed[0]
        if len(seed_list) > 1:
            parser.error("pass at most 1 value with --seed")
            return -1
        seed_value = seed_list[0]
    else:
        seed_value = None

    # It's possible to pass multiple --flags parameters, so collect them together and parse them.
    collected_flags = ""
    for flags in parsed.flags:
        collected_flags += f" {flags[0]}"
    flags = Flags(collected_flags)

    randomize(parsed.rom, flags, seed_value)
    return 0


if __name__ == "__main__":
    main()
