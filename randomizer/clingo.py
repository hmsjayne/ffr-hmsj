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

from collections import namedtuple

import clingo

from doslib.dos_utils import resolve_path

ClingoPlacement = namedtuple("ClingoPlacement", ["reward", "source"])


def solve_placement_for_seed(seed: int) -> tuple:
    """Create a random distribution for key items (KI).

    :param seed: The random number seed to use for the solver.
    :return: A list of tuples that contain item+location for each KI.
    """

    prg = clingo.Control()

    # Add your ASP programs
    prg.load(resolve_path("asp/KeyItemSolvingShip.lp"))
    prg.load(resolve_path("asp/KeyItemDataShip.lp"))

    # Set the seed and other configuration options
    prg.configuration.solve.models = 1  # Limit to one model
    prg.configuration.solver.sign_def = "rnd"
    prg.configuration.solver.seed = seed

    # Ground the program
    prg.ground([("base", [])])

    # Solve the problem
    result = []
    with prg.solve(yield_=True) as handle:
        for model in handle:
            result.append(model.symbols(shown=True))
            break  # Stop after finding the first model

    ki_placement = []
    for pairing in result[0]:
        pairing_str = str(pairing)
        pairing = ClingoPlacement(*pairing_str[5:len(pairing_str) - 1].split(","))
        ki_placement.append(pairing)

    return tuple(ki_placement)
