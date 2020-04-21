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

from stream.outputstream import OutputStream


def trivial_enemies(enemies: list):
    for index in range(0x80):
        enemies[index].max_hp = 1
        enemies[index].exp_reward = max(enemies[index].exp_reward, 1000)
        enemies[index].gil_reward = max(enemies[index].gil_reward, 1000)


def enable_early_magic_buy() -> dict:
    # Allow buying spells the class can before having the spell level
    buy_patch = OutputStream()
    buy_patch.put_u16(0xE013)

    display_patch = OutputStream()
    display_patch.put_u16(0xE020)
    return {
        0x45072: buy_patch.get_buffer(),
        0x455F8: display_patch.get_buffer()
    }
