import pytest

from randomizer.legacy_flags import LegacyFlagsError, parse_legacy_flags
from randomizer.options import RandomizerOptions


def test_parse_compact_default_flags():
    result = parse_legacy_flags("KSTGB10")

    assert result.style == "compact"
    assert result.options == RandomizerOptions(xp_rate_percent=100)
    assert result.warnings


def test_parse_compact_missing_flags():
    result = parse_legacy_flags("STGB10")

    assert result.options.shuffle_key_items is False
    assert result.options.randomize_shops is True
    assert result.options.randomize_treasure is True
    assert result.options.randomize_starting_gear is True
    assert result.options.randomize_bosses is True


def test_parse_compact_boss_and_extras():
    result = parse_legacy_flags("KSTGBNiR20")

    assert result.options.randomize_bosses is True
    assert result.options.new_item_distribution is True
    assert result.options.fiend_ribbons is True
    assert result.options.xp_rate_percent == 50


def test_parse_compact_boss_disabled():
    result = parse_legacy_flags("KSTG10")

    assert result.options.randomize_bosses is False


def test_parse_web_defaults():
    result = parse_legacy_flags("Xp15")

    assert result.style == "web"
    assert result.options == RandomizerOptions(xp_rate_percent=150)
    assert any("web" in warning.lower() for warning in result.warnings)


def test_parse_web_flags():
    result = parse_legacy_flags("OpSvTvGvBNiRXp15")

    assert result.options.shuffle_key_items is False
    assert result.options.randomize_shops is False
    assert result.options.randomize_treasure is False
    assert result.options.randomize_starting_gear is False
    assert result.options.randomize_bosses is False
    assert result.options.new_item_distribution is True
    assert result.options.fiend_ribbons is True
    assert result.options.xp_rate_percent == 150


def test_parse_web_xp_rate():
    assert parse_legacy_flags("Xp5").options.xp_rate_percent == 50
    assert parse_legacy_flags("Xp20").options.xp_rate_percent == 200
    assert parse_legacy_flags("Xp50").options.xp_rate_percent == 500


def test_parse_compact_approximate_xp():
    result = parse_legacy_flags("KSTGB15")

    assert result.options.xp_rate_percent == 70
    assert any("rounded" in warning for warning in result.warnings)


def test_empty_legacy_flags_are_rejected():
    with pytest.raises(LegacyFlagsError, match="remake"):
        parse_legacy_flags("")
