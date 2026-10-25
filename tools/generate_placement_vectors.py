#!/usr/bin/env python3
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

"""Generate native-clingo placement vectors for the WASM parity harness."""

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import clingo

from randomizer.placement_solver import (
    SIGN_DEFINITION,
    SOLVER_CONFIGURATION,
    ClingoSolver,
    validate_placement,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate placement parity vectors")
    parser.add_argument("--out", default="tests/fixtures/placement_parity.json")
    parser.add_argument("--seeds", type=int, default=100)
    args = parser.parse_args()

    solver = ClingoSolver()
    vectors = {}
    for seed in range(1, args.seeds + 1):
        pairs = solver.solve_seed(seed)
        validate_placement(pairs)
        vectors[str(seed)] = sorted([pair.item, pair.location] for pair in pairs)

    data = {
        "schema_version": 1,
        "solver": "clingo",
        "clingo_version": clingo.__version__,
        "configuration": SOLVER_CONFIGURATION,
        "sign_def": SIGN_DEFINITION,
        "models": 1,
        "seeds": vectors,
    }
    with open(args.out, "w") as output:
        json.dump(data, output, indent=2, sort_keys=True)
        output.write("\n")
    print(f"Wrote {args.out} ({len(vectors)} seeds)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
