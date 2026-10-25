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

"""Randomizer RNG interface.

Step 1 of the RNG migration is deliberately a thin wrapper around Python's
``random.Random``. The rest of the randomizer only depends on this interface,
so step 2 can replace the implementation with a portable algorithm without
touching the randomization stages.
"""

import random


class RNG:
    def __init__(self, seed=None):
        self._rng = random.Random()
        if seed is not None:
            self.seed(seed)

    def seed(self, seed) -> None:
        self._rng.seed(seed)

    def randrange(self, start, stop=None, step=1) -> int:
        if stop is None:
            if step != 1:
                raise ValueError("step must be 1 when stop is not supplied")
            return self._rng.randrange(start)
        return self._rng.randrange(start, stop, step)

    def randint(self, a: int, b: int) -> int:
        return self._rng.randint(a, b)

    def choice(self, sequence):
        return self._rng.choice(sequence)

    def shuffle(self, sequence) -> None:
        self._rng.shuffle(sequence)

    def sample(self, population, k: int):
        return self._rng.sample(population, k)

    def random(self) -> float:
        return self._rng.random()
