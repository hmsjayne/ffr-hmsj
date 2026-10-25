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

"""Key-item placement solver interface and the native clingo implementation.

The browser build uses clingo-wasm with the same configuration. Keeping this
behind an interface makes the solver replaceable later without touching the
randomizer stages.
"""

from collections import namedtuple
from typing import Protocol

import clingo

from doslib.dos_utils import resolve_path
from randomizer.rng import RNG

SOLVER_CONFIGURATION = "frumpy"
SIGN_DEFINITION = "rnd"

PlacementPair = namedtuple("PlacementPair", ["item", "location"])


class PlacementSolver(Protocol):
    def solve(self, rng: RNG) -> tuple:
        ...


def _program_paths() -> tuple[str, str]:
    return (
        resolve_path("asp/KeyItemSolvingShip.lp"),
        resolve_path("asp/KeyItemDataShip.lp"),
    )


class ClingoSolver:
    def __init__(self, configuration: str = SOLVER_CONFIGURATION):
        self.configuration = configuration

    def solve(self, rng: RNG) -> tuple:
        return self.solve_seed(rng.randint(0, 0xFFFFFFFF))

    def solve_seed(self, seed: int) -> tuple:
        prg = clingo.Control([f"--configuration={self.configuration}"])
        for path in _program_paths():
            prg.load(path)

        prg.configuration.solve.models = 1
        prg.configuration.solver.sign_def = SIGN_DEFINITION
        prg.configuration.solver.seed = seed
        prg.ground([("base", [])])

        pairs = None
        with prg.solve(yield_=True) as handle:
            for model in handle:
                pairs = _model_pairs(model)
                break

        if pairs is None:
            raise RuntimeError(f"Clingo found no placement model for seed {seed}")
        return tuple(pairs)


def _model_pairs(model) -> list:
    pairs = []
    for symbol in model.symbols(shown=True):
        text = str(symbol)
        if text.startswith("pair(") and text.endswith(")"):
            item, location = text[len("pair("):-1].split(",", 1)
            pairs.append(PlacementPair(item=item, location=location))
        elif text.startswith("notHas("):
            raise RuntimeError(f"Clingo returned an invalid placement: {text}")
    return pairs


def solve_placement_for_seed(seed: int) -> tuple:
    """Backward-compatible entry point used by older callers."""
    return ClingoSolver().solve_seed(seed)


def validate_placement(pairs) -> None:
    """Check the structural invariants shared by every placement solver."""
    if len(pairs) != 28:
        raise ValueError(f"Expected 28 placements, got {len(pairs)}")

    items = {pair.item for pair in pairs}
    locations = {pair.location for pair in pairs}
    if len(items) != len(pairs):
        raise ValueError("Placement contains duplicate items")
    if len(locations) != len(pairs):
        raise ValueError("Placement contains duplicate locations")

    fixed = [pair for pair in pairs if pair.item == "bottle"]
    if len(fixed) != 1 or fixed[0].location != "caravan":
        raise ValueError("Bottle must be placed at the caravan")
