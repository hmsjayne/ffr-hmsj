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

from doslib.gen.enemy import EnemyStats
from doslib.rom import Rom
from doslib.textblock import TextBlock
from randomizer.shuffledlist import ShuffledList


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
        self._sizes = []
        while not size_stream.is_eos():
            self._sizes.append(size_stream.get_u8())

        enemy_names = TextBlock(rom, 0x1DDD38, 0xc3)

        self._small_enemies = []
        self._large_enemies = []
        for index, size in enumerate(self._sizes):
            if index >= 0x80:
                break

            if index not in FormationRandomization.MINI_BOSS_IDS:
                if size == 0:
                    self._small_enemies.append(index)
                elif size == 1:
                    self._large_enemies.append(index)

        shuffled_small = ShuffledList(self._small_enemies, rng)
        shuffled_large = ShuffledList(self._large_enemies, rng)

        enemy_data_stream = rom.open_bytestream(0x1DE044, 0x1860)
        enemies = []
        scaled_enemies = []
        while not enemy_data_stream.is_eos():
            enemy = EnemyStats(enemy_data_stream)
            enemies.append(enemy)
            scaled_enemies.append(enemy)
        print(f"Count: {hex(len(scaled_enemies))}")

        for index in range(len(self._small_enemies)):
            original = shuffled_small.original(index)
            replacement = shuffled_small[index]
            scaled_enemies[original] = FormationRandomization.scale_enemy(enemies[replacement],
                                                                          enemies[original])

        for index in range(len(self._large_enemies)):
            original = shuffled_large.original(index)
            replacement = shuffled_large[index]
            scaled_enemies[original] = FormationRandomization.scale_enemy(enemies[replacement],
                                                                          enemies[original])

        for index, enemy in enumerate(scaled_enemies):
            print(f"{hex(index)}: {enemy_names[index]} -> {enemy.max_hp}")

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
