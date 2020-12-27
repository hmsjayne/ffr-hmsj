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
from doslib.enemy import *
from doslib.enemy import EnemyScript
from collections import namedtuple
from doslib.dos_utils import load_tsv
from stream.outputstream import OutputStream

NewScript = namedtuple("NewScript", ["iteration", "index", "name", "formation_size", "spell_chance", "ability_chance",
                                     "spell_1", "spell_2", "spell_3", "spell_4", "spell_5", "spell_6",
                                     "spell_7", "spell_8", "ability_1", "ability_2", "ability_3", "ability_4"])

MAX_BOSS_INDEX = 0xA0
MAX_SCRIPT_INDEX = 0x3C
FIEND_1_OFFSETS = [119, 121, 123, 125]
FIEND_2_OFFSETS = [120, 122, 124, 126]
FIEND_1_SCRIPT_OFFSETS = [34, 36, 38, 40]
FIEND_2_SCRIPT_OFFSETS = [35, 37, 39, 41]
FIEND_1_ENCOUNTERS = [122, 121, 120, 119]
FIEND_2_ENCOUNTERS = [115, 116, 117, 118]


class BossData:
    def __init__(self, rom: Rom):
        # Initialize data - the 8 boss spots that are changed, as well as the name, graphics and script blocks
        # If we don't randomize anything, get_patches() should return the same data we load in
        name_pointers = rom.open_bytestream(0x1DDD38, 0x280)
        self.name_pointers = []
        while not name_pointers.is_eos():
            self.name_pointers.append(EnemyName(name_pointers))

        graphics_pointers = rom.open_bytestream(0x2227D8, 0x780)
        self.graphics_pointers = []
        while not graphics_pointers.is_eos():
            self.graphics_pointers.append(EnemyGraphics(graphics_pointers))

        attack_animations = rom.open_bytestream(0x223540, 0xA0)
        self.attack_animations = []
        while not attack_animations.is_eos():
            self.attack_animations.append(attack_animations.get_u8())

        enemy_script_stream = rom.open_bytestream(0x22F17C, 0x450)
        self.scripts = []
        while not enemy_script_stream.is_eos():
            self.scripts.append(EnemyScript(enemy_script_stream))

        self.boss_data = {}
        for script in load_tsv("data/BossScriptData.tsv"):
            entry = NewScript(*script)
            if entry.name not in self.boss_data:
                self.boss_data[entry.name] = [None, None, None]
            self.boss_data[entry.name][entry.iteration] = entry
        self.boss_list = list(self.boss_data.keys())

        # Finally, load in the script data from the ROM - we can read in the tsv if/when randomize gets called

    def randomize_bosses(self, encounters: list, enemy_data: list, rng: random.Random):
        boss_choices = rng.sample(self.boss_list, 4)
        rng.shuffle(boss_choices)
        new_fiend1s = [self.boss_data[boss_choices[0]][0], self.boss_data[boss_choices[1]][0],
                       self.boss_data[boss_choices[2]][1], self.boss_data[boss_choices[3]][1]]

        new_fiend2s = [self.boss_data[boss_choices[0]][2], self.boss_data[boss_choices[1]][2],
                       self.boss_data[boss_choices[2]][2], self.boss_data[boss_choices[3]][2]]

        for fiend_index in range(4):
            fiend1 = new_fiend1s[fiend_index]
            fiend2 = new_fiend2s[fiend_index]

            fiend1_encounter = FIEND_1_ENCOUNTERS[fiend_index]
            fiend2_encounter = FIEND_2_ENCOUNTERS[fiend_index]
            encounters[fiend1_encounter].config = fiend1.formation_size
            encounters[fiend2_encounter].config = fiend2.formation_size

            self.graphics_pointers[FIEND_1_OFFSETS[fiend_index]] = self.graphics_pointers[fiend1.index]
            self.graphics_pointers[FIEND_2_OFFSETS[fiend_index]] = self.graphics_pointers[fiend2.index]
            self.attack_animations[FIEND_1_OFFSETS[fiend_index]] = self.attack_animations[fiend1.index]
            self.attack_animations[FIEND_2_OFFSETS[fiend_index]] = self.attack_animations[fiend2.index]
            self.name_pointers[FIEND_1_OFFSETS[fiend_index]] = self.name_pointers[fiend1.index]
            self.name_pointers[FIEND_2_OFFSETS[fiend_index]] = self.name_pointers[fiend2.index]

            fiend1_script = FIEND_1_SCRIPT_OFFSETS[fiend_index]
            fiend2_script = FIEND_2_SCRIPT_OFFSETS[fiend_index]

            fiend1_spells = [fiend1.spell_1, fiend1.spell_2, fiend1.spell_3, fiend1.spell_4,
                             fiend1.spell_5, fiend1.spell_6, fiend1.spell_7, fiend1.spell_8]
            fiend2_spells = [fiend2.spell_1, fiend2.spell_2, fiend2.spell_3, fiend2.spell_4,
                             fiend2.spell_5, fiend2.spell_6, fiend2.spell_7, fiend2.spell_8]

            fiend1_abilities = [fiend1.ability_1, fiend1.ability_2, fiend1.ability_3, fiend1.ability_4]
            fiend2_abilities = [fiend2.ability_1, fiend2.ability_2, fiend2.ability_3, fiend2.ability_4]

            self.scripts[fiend1_script].spell_chance = fiend1.spell_chance
            self.scripts[fiend2_script].spell_chance = fiend2.spell_chance
            self.scripts[fiend1_script].ability_chance = fiend1.ability_chance
            self.scripts[fiend2_script].ability_chance = fiend2.ability_chance
            for spell_index in range(8):
                self.scripts[fiend1_script].spells[spell_index] = fiend1_spells[spell_index]
                self.scripts[fiend2_script].spells[spell_index] = fiend2_spells[spell_index]

            for ability_index in range(4):
                self.scripts[fiend1_script].abilities[ability_index] = fiend1_abilities[ability_index]
                self.scripts[fiend2_script].abilities[ability_index] = fiend2_abilities[ability_index]

            old_enemy_index_1 = fiend1.index
            old_enemy_index_2 = fiend1.index
            if old_enemy_index_1 in FIEND_1_OFFSETS:
                old_enemy_index_2 += 1

            ability_list = [
                [FIEND_1_OFFSETS[fiend_index],
                 old_enemy_index_1],
                [FIEND_2_OFFSETS[fiend_index],
                 old_enemy_index_2]
            ]
            for idx_pair in ability_list:
                enemy_data[idx_pair[0]].status_atk_elem = enemy_data[idx_pair[1]].status_atk_elem
                enemy_data[idx_pair[0]].status_atk_ailment = enemy_data[idx_pair[1]].status_atk_ailment
                enemy_data[idx_pair[0]].elem_weakness = enemy_data[idx_pair[1]].elem_weakness
                enemy_data[idx_pair[0]].elem_resists = enemy_data[idx_pair[1]].elem_resists

    def get_patches(self):
        out_name_pointers = OutputStream()
        for ptr in self.name_pointers:
            ptr.write(out_name_pointers)

        out_graphics_pointers = OutputStream()
        for ptr in self.graphics_pointers:
            ptr.write(out_graphics_pointers)

        out_attack_animations = OutputStream()
        for ptr in self.attack_animations:
            out_attack_animations.put_u8(ptr)

        out_scripts = OutputStream()
        for ptr in self.scripts:
            ptr.write(out_scripts)

        return {
            0x1DDD38: out_name_pointers.get_buffer(),
            0x2227D8: out_graphics_pointers.get_buffer(),
            0x223540: out_attack_animations.get_buffer(),
            0x22F17C: out_scripts.get_buffer()
        }
