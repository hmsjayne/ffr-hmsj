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
from collections import namedtuple

from doslib.dos_utils import load_tsv
from doslib.spell import SpellData
from doslib.spells import Spells

ChestData = namedtuple("ChestData", ["chest_index", "type", "contents", "description", "map", "grade", "notes"])

MapToArea = namedtuple("MapToArea", ["map_index", "name", "area"])


class SpellGenerator(object):
    def __init__(self, seed: str, spells: Spells):
        self.rng = random.Random()
        self.rng.seed(seed)

        self.maps_to_area = {}
        for map_area in load_tsv("data/MapToArea.tsv"):
            map_area_data = MapToArea(*map_area)
            self.maps_to_area[map_area_data.map_index] = map_area_data.area

        self.area_weights = {}
        for area_weight in load_tsv("data/AreaWeights.tsv"):
            self.area_weights[area_weight[0]] = area_weight[1:]

        self.spell_grades = {}
        for spell in spells.spell_data:
            if spell.grade is None:
                # Skip
                continue

            if spell.grade not in self.spell_grades:
                self.spell_grades[spell.grade] = []
            self.spell_grades[spell.grade].append(spell)

    def get_inventory(self, map_index: int, school: str) -> SpellData:
        area = self.maps_to_area[map_index]
        area_weight = self.area_weights[area]
        index_to_letter = ["S", "A", "B", "C", "D", "E", "F"]

        spell_pool = []
        while len(spell_pool) < 1:
            chance = self.rng.randint(0, 100)
            pick = None
            for index, score in enumerate(area_weight):
                chance -= score
                if chance <= 0:
                    pick = index
                    break
            grade_letter = index_to_letter[pick]

            # If there's none at this letter grade, try to pick again
            if grade_letter not in self.spell_grades:
                continue

            spell_pool = []
            for spell in self.spell_grades[grade_letter]:
                if spell.school == school:
                    spell_pool.append(spell)

            if len(spell_pool) < 1:
                # Ensure there are still spells
                is_empty = True
                for spell_grade, spells in self.spell_grades.items():
                    if len(spells) > 0:
                        is_empty = False
                        break
                if is_empty:
                    raise RuntimeError("Out of spells!")
                else:
                    continue

            self.rng.shuffle(spell_pool)
            picked = spell_pool.pop()
            self.spell_grades[grade_letter].remove(picked)

            return picked


def _grade_to_score(grade: str) -> int:
    grades = {
        "S": 100,
        "A": 85,
        "B": 75,
        "C": 40,
        "D": 20,
    }
    base_grade = grades[grade[0]]
    if len(grade) > 1:
        if grade[1] == '+':
            return base_grade + 5
        else:
            return base_grade - 5
    return base_grade
