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

from subprocess import run, PIPE
from math import pow
import json

"""Note: this requires an installation of Clingo 4.5 or better"""


def shuffle_key_items(seed: int):
    command = ["clingo", "asp/KeyItemSolving.lp", "asp/KeyItemData.lp"]
    command.append("--sign-def=3")
    command.append("--seed=" + str(seed))
    command.append("--outf=2")
    clingo_out = json.loads(run(command, stdout=PIPE).stdout)
    pairings = clingo_out['Call'][0]['Witnesses'][0]['Value']

    # All pairings are of the form "pair(item,location)" - need to parse the info
    print(f"data: {pairings}")