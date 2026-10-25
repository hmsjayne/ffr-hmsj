import random

import pytest

from randomizer.rng import RNG


@pytest.mark.parametrize("seed", [1, "seed", "  Voyage of the Cactuar  "])
def test_rng_matches_python_random(seed):
    expected = random.Random(seed)
    actual = RNG(seed)

    assert [actual.randint(0, 100) for _ in range(50)] == [
        expected.randint(0, 100) for _ in range(50)
    ]
    assert [actual.randrange(10, 50, 3) for _ in range(20)] == [
        expected.randrange(10, 50, 3) for _ in range(20)
    ]
    assert [actual.choice(["a", "b", "c"]) for _ in range(20)] == [
        expected.choice(["a", "b", "c"]) for _ in range(20)
    ]
    assert [actual.random() for _ in range(10)] == [expected.random() for _ in range(10)]


def test_rng_shuffle_and_sample_match_python_random():
    expected = random.Random("seed")
    actual = RNG("seed")

    expected_values = list(range(20))
    actual_values = list(range(20))
    expected.shuffle(expected_values)
    actual.shuffle(actual_values)

    assert actual_values == expected_values
    assert actual.sample(range(100), 10) == expected.sample(range(100), 10)


def test_rng_seed_resets_sequence():
    rng = RNG("first")
    first = [rng.randint(0, 1000) for _ in range(10)]

    rng.seed("first")
    assert [rng.randint(0, 1000) for _ in range(10)] == first

    rng.seed("second")
    assert [rng.randint(0, 1000) for _ in range(10)] != first


def test_rng_randrange_without_stop():
    expected = random.Random(1)
    actual = RNG(1)

    assert [actual.randrange(10) for _ in range(20)] == [
        expected.randrange(10) for _ in range(20)
    ]

    with pytest.raises(ValueError):
        actual.randrange(10, step=2)
