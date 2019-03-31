#  Copyright 2019 Stella Mazeika
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
from collections import namedtuple
from subprocess import run, PIPE

"""Note: this requires an installation of Clingo 4.5 or better"""


def solve_key_item_placement(seed: int):
    command = [
        "clingo", "asp/KeyItemSolving.lp", "asp/KeyItemData.lp",
        "--sign-def=3",
        "--seed=" + str(seed),
        "--outf=2"
    ]

    clingo_out = json.loads(run(command, stdout=PIPE).stdout)
    pairings = clingo_out['Call'][0]['Witnesses'][0]['Value']

    # All pairings are of the form "pair(item,location)" - need to parse the info
    Placement = namedtuple("Placement", ["item", "location"])

    ki_placement = []
    for pairing in pairings:
        pairing = Placement(*pairing[5:len(pairing) - 1].split(","))
        ki_placement.append(pairing)

    return tuple(ki_placement)
