import pytest

from randomizer.options import (
    ALGORITHM_VERSION,
    DEFAULT_OPTIONS,
    RandomizerOptions,
)


def test_default_options():
    assert DEFAULT_OPTIONS.shuffle_key_items is True
    assert DEFAULT_OPTIONS.randomize_shops is True
    assert DEFAULT_OPTIONS.randomize_treasure is True
    assert DEFAULT_OPTIONS.randomize_starting_gear is True
    assert DEFAULT_OPTIONS.randomize_bosses is True
    assert DEFAULT_OPTIONS.new_item_distribution is False
    assert DEFAULT_OPTIONS.fiend_ribbons is False
    assert DEFAULT_OPTIONS.xp_rate_percent == 150
    assert DEFAULT_OPTIONS.debug is False
    assert DEFAULT_OPTIONS.short_code() == "KSTGBXp150"
    assert ALGORITHM_VERSION == 2


def test_options_round_trip():
    options = RandomizerOptions(
        shuffle_key_items=False,
        randomize_shops=False,
        randomize_treasure=False,
        randomize_starting_gear=False,
        randomize_bosses=False,
        new_item_distribution=True,
        fiend_ribbons=True,
        xp_rate_percent=200,
        debug=True,
    )

    assert RandomizerOptions.from_dict(options.to_dict()) == options
    assert options.public_dict()["new_item_distribution"] is True
    assert "debug" not in options.public_dict()


@pytest.mark.parametrize("value", [49, 55, 501, 0, -10])
def test_xp_rate_validation(value):
    with pytest.raises(ValueError):
        RandomizerOptions(xp_rate_percent=value)


def test_xp_rate_must_be_integer():
    with pytest.raises(TypeError):
        RandomizerOptions(xp_rate_percent=150.0)


def test_unknown_option_is_rejected():
    with pytest.raises(ValueError, match="Unknown option"):
        RandomizerOptions.from_dict({"not_an_option": True})


def test_short_code_includes_non_default_options():
    options = RandomizerOptions(
        shuffle_key_items=False,
        randomize_bosses=False,
        new_item_distribution=True,
        fiend_ribbons=True,
        xp_rate_percent=200,
    )

    assert options.short_code() == "STGNiRXp200"
