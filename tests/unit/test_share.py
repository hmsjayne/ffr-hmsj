import pytest

from randomizer.options import DEFAULT_OPTIONS, RandomizerOptions
from randomizer.share import (
    ShareLinkError,
    build_filename,
    encode_share_fragment,
    parse_share_fragment,
)


def test_encode_default_options_uses_only_seed():
    fragment = encode_share_fragment("test", DEFAULT_OPTIONS)

    assert fragment == "#v=2&seed=test"


def test_encode_and_parse_non_default_options():
    options = RandomizerOptions(
        shuffle_key_items=False,
        randomize_shops=False,
        new_item_distribution=True,
        fiend_ribbons=True,
        xp_rate_percent=200,
    )

    fragment = encode_share_fragment("Voyage of the Cactuar", options)
    parsed = parse_share_fragment(fragment)

    assert parsed.seed == "Voyage of the Cactuar"
    assert parsed.options == options
    assert parsed.warnings == []
    assert parsed.legacy is False


def test_parse_unknown_option_warns():
    parsed = parse_share_fragment("#v=2&seed=test&mystery=1")

    assert parsed.options == DEFAULT_OPTIONS
    assert any("mystery" in warning for warning in parsed.warnings)


def test_parse_legacy_link_rewrites_to_new_format():
    parsed = parse_share_fragment("#seed=test&flags=OpSvTvGvBNiRXp15")

    assert parsed.legacy is True
    assert parsed.options.shuffle_key_items is False
    assert parsed.options.randomize_bosses is False
    assert parsed.rewritten_fragment is not None
    asserted = parse_share_fragment(parsed.rewritten_fragment)
    assert asserted.seed == "test"
    assert asserted.options == parsed.options


def test_parse_legacy_compact_link_rewrites():
    parsed = parse_share_fragment("#seed=test&flags=STGB10")

    assert parsed.legacy is True
    assert parsed.options.shuffle_key_items is False
    assert parsed.rewritten_fragment is not None


@pytest.mark.parametrize("fragment", [
    "#v=1&seed=test",
    "#v=2",
    "#v=2&seed=test&xp=55",
    "#seed=test",
    "#v=2&seed=test&keys=maybe",
])
def test_parse_invalid_links(fragment):
    with pytest.raises(ShareLinkError):
        parse_share_fragment(fragment)


def test_build_filename():
    options = RandomizerOptions(xp_rate_percent=200)

    assert build_filename("Voyage of the Cactuar", options) == (
        "ff1-dos_v2_KSTGBXp200_Voyage-of-the-Cactuar.gba"
    )
