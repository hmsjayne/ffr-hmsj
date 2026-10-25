from randomizer.flags import Flags


def test_flags_defaults_and_encoding():
    flags = Flags()

    assert flags.no_shuffle is False
    assert flags.standard_shops is False
    assert flags.standard_treasure is False
    assert flags.default_start_gear is False
    assert flags.boss_shuffle is False
    assert flags.new_items is False
    assert flags.fiend_ribbons is False
    assert flags.debug is False
    assert flags.scale_levels == 1.0
    assert flags.encode() == "KSTGB10"


def test_flags_encoding_is_current_behavior_baseline():
    # These values intentionally document the pre-Phase-2 encoding. They will
    # change when flags are made canonical and round-trippable.
    flags = Flags()
    flags.no_shuffle = True
    assert flags.encode() == "STGB10"

    flags = Flags()
    flags.boss_shuffle = True
    assert flags.encode() == "KSTG10"

    flags = Flags()
    flags.scale_levels = 0.5
    assert flags.encode() == "KSTGB5"


def test_flags_string_contains_all_properties():
    flags = Flags()
    rendered = str(flags)

    for name in ("no_shuffle", "standard_shops", "standard_treasure", "boss_shuffle"):
        assert f"{name}=" in rendered
