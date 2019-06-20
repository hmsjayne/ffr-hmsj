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
import copy
from random import Random

from doslib.gen.enemy import EnemyStats, Encounter, EncounterGroup
from doslib.rom import Rom
from doslib.textblock import TextBlock
from randomizer.shuffledlist import ShuffledList
from stream.outputstream import OutputStream


class FormationRandomization(object):
    FLYING_MONSTER_IDS = [0x51, 0x52, 0x52, 0xA2, 0x3E, 0x3F, 0xBB]

    MINI_BOSS_IDS = [
        0xf,  # Pirate(s)
        0x69,  # Garland
        0x71,  # Astos
        0x76  # Death Machine
    ]

    def __init__(self, rom: Rom, rng: Random):
        size_stream = rom.open_bytestream(0x223644, 0xc3)
        sizes = []
        while not size_stream.is_eos():
            sizes.append(size_stream.get_u8())

        small_enemies = []
        large_enemies = []

        enemy_id_map = []
        for index, size in enumerate(sizes):
            enemy_id_map.append(index)

            if index >= 0x80:
                break

            if index not in FormationRandomization.MINI_BOSS_IDS:
                if size == 0:
                    small_enemies.append(index)
                elif size == 1:
                    large_enemies.append(index)

        shuffled_small = ShuffledList(small_enemies, rng)
        shuffled_large = ShuffledList(large_enemies, rng)

        enemy_data_stream = rom.open_bytestream(0x1DE044, 0x1860)
        enemies = []
        scaled_enemies = []
        while not enemy_data_stream.is_eos():
            enemy = EnemyStats(enemy_data_stream)
            enemies.append(enemy)
            scaled_enemies.append(enemy)

        for index in range(len(small_enemies)):
            original = shuffled_small.original(index)
            replacement = shuffled_small[index]
            scaled_enemy = FormationRandomization.scale_enemy(enemies[original],
                                                              enemies[replacement])
            scaled_enemies[replacement] = scaled_enemy
            enemy_id_map[original] = replacement

        for index in range(len(large_enemies)):
            original = shuffled_large.original(index)
            replacement = shuffled_large[index]
            scaled_enemy = FormationRandomization.scale_enemy(enemies[original],
                                                              enemies[replacement])
            scaled_enemies[replacement] = scaled_enemy
            enemy_id_map[original] = replacement

        self._scaled_enemies_out = OutputStream()
        for enemy in scaled_enemies:
            enemy.write(self._scaled_enemies_out)

        formations_stream = rom.open_bytestream(0x2288B4, 0x14 * 0x171)
        self._formations_out = OutputStream()
        while not formations_stream.is_eos():
            formation = Encounter(formations_stream)

            has_land = False
            has_flying = False
            for index, group in enumerate(formation.groups):
                if group.enemy_id < len(enemy_id_map):
                    group.enemy_id = enemy_id_map[group.enemy_id]

                if group.max_count == 0:
                    group.enemy_id = 0

                if group.enemy_id in FormationRandomization.FLYING_MONSTER_IDS:
                    has_flying = True
                else:
                    has_land = True

            if formation.config in [0x0, 0x05]:
                if has_flying and has_land:
                    # Both land and flying -> Mixed
                    formation.config = 0x5
                else:
                    # Even if they're all flying, they still get mapped to "1-9 small"
                    formation.config = 0x0

            # Save the new formations
            formation.write(self._formations_out)

    def patches(self) -> dict:
        return {
            0x1DE044: self._scaled_enemies_out.get_buffer(),
            0x2288B4: self._formations_out.get_buffer()
        }

    @staticmethod
    def scale_enemy(from_enemy: EnemyStats, to_enemy: EnemyStats) -> EnemyStats:
        self_exp = from_enemy.exp_reward if from_enemy.exp_reward > 1 else 1620
        other_exp = to_enemy.exp_reward if to_enemy.exp_reward > 1 else 1620
        ratio = other_exp / self_exp

        estimate_damage = ((to_enemy.acc / 200) * to_enemy.atk) * to_enemy.hit_count
        target_attack = (estimate_damage / (from_enemy.acc / 200)) / from_enemy.hit_count
        new_hit_count = from_enemy.hit_count
        if target_attack > 220:
            if new_hit_count == 1:
                new_hit_count = 2
                target_attack = min(target_attack / 2, 220)

        scaled_enemy = copy.deepcopy(from_enemy)
        scaled_enemy.exp_reward = to_enemy.exp_reward if from_enemy.exp_reward > 1 else from_enemy.exp_reward
        scaled_enemy.gil_reward = int(from_enemy.gil_reward * ratio) if from_enemy.gil_reward > 1 else 1
        scaled_enemy.hp = int(from_enemy.max_hp * ratio)
        scaled_enemy.intel = min(int(from_enemy.intel * ratio), 160)
        scaled_enemy.attack = min(int(target_attack), 220)
        scaled_enemy.hit_count = int(new_hit_count)
        return scaled_enemy
