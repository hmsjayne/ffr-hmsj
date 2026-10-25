import pytest

from randomizer.rng import RNG


def test_rng_known_sequence():
    rng = RNG("seed")

    assert [rng.randint(0, 100) for _ in range(20)] == [
        73, 81, 43, 39, 65, 32, 11, 76, 57, 75,
        62, 82, 10, 58, 86, 88, 89, 49, 92, 37,
    ]


def test_rng_known_randrange_sequence():
    rng = RNG("seed")

    assert [rng.randrange(10, 50, 3) for _ in range(10)] == [
        37, 40, 25, 22, 34, 22, 13, 37, 31, 37,
    ]


def test_rng_known_choice_sequence():
    rng = RNG("seed")

    assert [rng.choice(["a", "b", "c"]) for _ in range(20)] == [
        "c", "c", "b", "b", "c", "b", "a", "c", "b", "c",
        "b", "c", "a", "b", "c", "c", "c", "b", "c", "b",
    ]


def test_rng_known_float_sequence():
    rng = RNG("seed")

    assert [rng.random() for _ in range(10)] == [
        0.5748232873819783,
        0.3372058416920768,
        0.8848134004426077,
        0.9225433685794598,
        0.5082839522947902,
        0.9791101894753879,
        0.9318231165342203,
        0.45151651566016393,
        0.5891460019142982,
        0.49117581280624434,
    ]


def test_rng_known_shuffle_and_sample():
    rng = RNG("seed")
    values = list(range(20))
    rng.shuffle(values)

    assert values == [15, 0, 11, 2, 3, 6, 8, 5, 19, 14, 12, 13, 7, 17, 1, 4, 16, 9, 10, 18]

    rng = RNG("seed")
    assert rng.sample(list(range(100)), 10) == [73, 82, 45, 42, 69, 37, 17, 83, 65, 84]


def test_rng_known_max_integer_sequence():
    rng = RNG("test")

    assert [rng.randint(0, 0xFFFFFFFF) for _ in range(5)] == [
        1655031343,
        2003141121,
        3714344073,
        2703493369,
        3530671265,
    ]


def test_rng_seed_resets_sequence():
    rng = RNG("first")
    first = [rng.randint(0, 1000) for _ in range(10)]

    rng.seed("first")
    assert [rng.randint(0, 1000) for _ in range(10)] == first

    rng.seed("second")
    assert [rng.randint(0, 1000) for _ in range(10)] != first


def test_rng_seed_accepts_bytes_and_integer():
    assert [RNG(b"seed").randint(0, 1000) for _ in range(5)] == [
        RNG("seed").randint(0, 1000) for _ in range(5)
    ]
    assert RNG(123).randint(0, 1000) == RNG(123).randint(0, 1000)


def test_rng_invariants():
    rng = RNG("invariants")

    values = [rng.randint(3, 5) for _ in range(1000)]
    assert set(values) == {3, 4, 5}
    assert all(3 <= value <= 5 for value in values)

    values = [rng.randrange(100) for _ in range(1000)]
    assert all(0 <= value < 100 for value in values)

    sampled = rng.sample(list(range(100)), 25)
    assert len(sampled) == 25
    assert len(set(sampled)) == 25

    shuffled = list(range(50))
    rng.shuffle(shuffled)
    assert sorted(shuffled) == list(range(50))

    floats = [rng.random() for _ in range(100)]
    assert all(0.0 <= value < 1.0 for value in floats)


def test_rng_errors():
    rng = RNG("errors")

    with pytest.raises(IndexError):
        rng.choice([])

    with pytest.raises(ValueError):
        rng.sample([1, 2], 3)

    with pytest.raises(ValueError):
        rng.sample([1, 2], -1)

    with pytest.raises(ValueError):
        rng.randrange(0, 10, 0)

    with pytest.raises(ValueError):
        rng.randrange(10, 0)

    with pytest.raises(ValueError):
        rng.randrange(10, step=2)

    with pytest.raises(TypeError):
        RNG(1.5)
