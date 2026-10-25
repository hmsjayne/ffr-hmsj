import json
from pathlib import Path

import pytest

from randomizer.placement_solver import (
    SIGN_DEFINITION,
    SOLVER_CONFIGURATION,
    ClingoSolver,
    PlacementPair,
    validate_placement,
)

FIXTURE = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "placement_parity.json").read_text()
)


def test_placement_fixture_metadata():
    assert FIXTURE["solver"] == "clingo"
    assert FIXTURE["configuration"] == SOLVER_CONFIGURATION
    assert FIXTURE["sign_def"] == SIGN_DEFINITION
    assert FIXTURE["models"] == 1
    assert len(FIXTURE["seeds"]) == 100


@pytest.mark.parametrize("seed", range(1, 101))
def test_native_solver_matches_parity_fixture(seed):
    pairs = ClingoSolver().solve_seed(seed)
    validate_placement(pairs)

    actual = sorted([pair.item, pair.location] for pair in pairs)
    assert actual == FIXTURE["seeds"][str(seed)]


def test_solver_is_deterministic():
    first = ClingoSolver().solve_seed(42)
    second = ClingoSolver().solve_seed(42)

    assert first == second


def test_validate_placement_rejects_duplicate_items():
    pairs = [PlacementPair(item="a", location=f"l{index}") for index in range(28)]

    with pytest.raises(ValueError, match="duplicate items"):
        validate_placement(pairs)


def test_validate_placement_rejects_missing_bottle():
    pairs = [PlacementPair(item=f"i{index}", location=f"l{index}") for index in range(28)]

    with pytest.raises(ValueError, match="Bottle"):
        validate_placement(pairs)
