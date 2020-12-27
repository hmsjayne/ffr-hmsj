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

import json
from sys import platform
from collections import namedtuple
from subprocess import PIPE, run

ClingoPlacement = namedtuple("ClingoPlacement", ["reward", "source"])


def solve_placement_for_seed(seed: int) -> tuple:
    """Create a random distribution for key items (KI).

    Note: this requires an installation of Clingo 4.5 or better

    :param seed: The random number seed to use for the solver.
    :return: A list of tuples that contain item+location for each KI.
    """

    if platform.startswith("win"):
        clingo_name = "clingo-win.exe"
    elif platform.startswith("darwin"):
        clingo_name = "clingo-darwin"
    else:
        clingo_name = "clingo-linux"

    command = [
        f"clingo/{clingo_name}", "asp/KeyItemSolvingShip.lp", "asp/KeyItemDataShip.lp",
        "--sign-def=rnd",
        "--seed=" + str(seed),
        "--outf=2"
    ]

    try:
        clingo_out = json.loads(run(command, stdout=PIPE).stdout)
    except:
        command[0] = "clingo"
        clingo_out = json.loads(run(command, stdout=PIPE).stdout)
    pairings = clingo_out['Call'][0]['Witnesses'][0]['Value']

    ki_placement = []
    for pairing in pairings:
        pairing = ClingoPlacement(*pairing[5:len(pairing) - 1].split(","))
        ki_placement.append(pairing)

    return tuple(ki_placement)
